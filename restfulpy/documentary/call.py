import io
import re
from urllib.parse import parse_qs
from os import path

import ujson
import yaml
from nanohttp.helpers import parse_any_form

from .constants import  URL_PARAMETER_PATTERN, CONTENT_TYPE_PATTERN
from ..fieldinfo import FieldInfo


class Response:
    _status = None
    status_code = None
    status_text = None
    content_type = None
    encoding = None

    def __init__(self, status=None, headers=None, body=None, status_code=None, status_text=None):
        self.status_code = status_code
        self.status_text = status_text
        if status:
            self.status = status

        if isinstance(body, dict):
            body = ujson.encode(body)

        self.buffer = body.splitlines() if body else []
        self.headers = headers or []

        for i in self.headers:
            k, v = i.split(': ') if isinstance(i, str) else i
            if k == 'Content-Type':
                match = CONTENT_TYPE_PATTERN.match(v)
                if match:
                    self.content_type, self.encoding = match.groups()
                break

    def load(self, wsgi_response):
        for chunk in wsgi_response:
            self.buffer.append(chunk)
        return self.buffer

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        if ' ' in value:
            parts = value.split(' ')
            status_code, self.status_text = parts[0], ' '.join(parts[1:])
        else:
            status_code = value
        self.status_code = int(status_code)

    def to_dict(self):
        return dict(
            status_code=self.status_code,
            status_text=self.status_text,
            headers=[f'{k}: {v}' for k, v in self.headers],
            body=self.json if self.content_type == 'application/json' else self.text
        )

    @property
    def body(self):
        payload = b''.join(self.buffer)
        return payload

    @property
    def text(self):
        return self.body.decode()

    @property
    def json(self):
        return ujson.loads(self.body)


class ApiCall:
    response = None
    url_parameters = None
    query_string = None

    def __init__(self, url, verb='GET', title=None, description=None, query_string=None,
                 form=None, role=None, expected_status=None, url_parameters=None, response=None):
        self.description = description
        self.query_string = query_string
        self.form = form
        self.url = url
        self.title = title
        self.verb = verb
        self.role = role
        self.expected_status = expected_status
        self.url_parameters = url_parameters
        if response:
            self.response = response if isinstance(response, Response) else Response(**response)

    @classmethod
    def from_environ(cls, environ, *args, **kwargs):
        if environ['QUERY_STRING']:
            kwargs['query_string'] = {
                k: v[0] if len(v) == 1 else v for k, v in parse_qs(
                    environ['QUERY_STRING'],
                    keep_blank_values=True,
                    strict_parsing=False
                ).items()
            }

        kwargs['description'] = environ.get('TEST_CASE_DESCRIPTION', None)
        kwargs['title'] = environ['TEST_CASE_TITLE']
        kwargs['verb'] = environ['REQUEST_METHOD'].upper()
        kwargs['role'] = environ.get('TEST_CASE_ROLE', None)

        status = environ.get('TEST_CASE_EXPECTED_STATUS', None)
        kwargs['expected_status'] = int(status) if status else status

        url = environ['PATH_INFO']
        if URL_PARAMETER_PATTERN.search(url):
            # noinspection PyTypeChecker
            url_parameters = dict()
            for k, v in URL_PARAMETER_PATTERN.findall(url):
                url_parameters[k] = v
                url = re.sub(f'{k}:\s?', '', url)
            environ['PATH_INFO'] = url
        else:
            url_parameters = None
        kwargs['url_parameters'] = url_parameters

        fields = environ.get('TEST_CASE_FIELDS')
        fields = ujson.loads(fields) if fields else {}
        kwargs['form'] = cls.parse_form(environ, fields=fields)
        return cls(url, *args, **kwargs)

    @staticmethod
    def parse_form(environ, fields):
        form_file = environ['wsgi.input']
        content_length = int(environ.get('CONTENT_LENGTH', 0))
        form_data = form_file.read(content_length)
        monkey_form_file = io.BytesIO(form_data)
        environ['wsgi.input'] = monkey_form_file
        form = parse_any_form(environ)
        monkey_form_file.seek(0)
        return {k: ApiField(v, **fields.get(k, {})) for k, v in form.items()} if form else None

    def start_response_wrapper(self, start_response):
        def start_response_profiler(status, headers):
            self.response = Response(status, headers)
            return start_response(status, headers)
        return start_response_profiler

    def to_dict(self):
        return dict(
            title=self.title,
            url=self.url,
            url_parameters=self.url_parameters,
            verb=self.verb,
            query_string=self.query_string,
            response=self.response.to_dict(),
            form={k: v.to_dict() for k, v in self.form.items()} if self.form else None,
            role=self.role,
            expected_status=self.expected_status,
            description=self.description
        )

    def dump(self, file):
        yaml.dump(self.to_dict(), file, default_flow_style=False)

    def save(self, directory):
        with open(path.join(directory, self.filename), 'w') as f:
            self.dump(f)

    @property
    def filename(self):
        url = self.url.strip('/').replace('/', '-')
        title = self.title.replace(' ', '-')
        return f'{url}-{self.verb}-{self.response.status}-{title}.yml'.replace(' ', '-')

    @classmethod
    def load(cls, file):
        data = yaml.load(file)
        return cls(**data)


class ApiField(FieldInfo):
    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        import builtins
        t = getattr(builtins, self.type_, str)
        self.value = t(value)
