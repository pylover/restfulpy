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

    def __init__(self, status=None, headers=None):
        self.status = status
        self.buffer = []
        self.headers = headers or []

        for k, v in self.headers:
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

    def dump(self):
        return dict(
            status_code=self.status_code,
            status_text=self.status_text,
            headers=self.headers,
            body=self.text
        )

    @property
    def body(self):
        return b''.join(self.buffer)

    @property
    def text(self):
        return self.body.decode()

    @property
    def json(self):
        return ujson.loads(self.buffer)


class ApiCall:
    response = None
    url_parameters = None
    query_string = None

    def __init__(self, application, environ, start_response):
        self.application = application
        self.environ = environ
        self.start_response = start_response

        if URL_PARAMETER_PATTERN.search(self.url):
            # noinspection PyTypeChecker
            self.url_parameters = dict()
            url = self.url
            for k, v in URL_PARAMETER_PATTERN.findall(self.url):
                self.url_parameters[k] = v
                url = re.sub(f'{k}:\s?', '', url)
            self.url = url

        if self.environ['QUERY_STRING']:
            self.query_string = {
                k: v[0] if len(v) == 1 else v for k, v in parse_qs(
                    self.environ['QUERY_STRING'],
                    keep_blank_values=True,
                    strict_parsing=False
                ).items()
            }

        fields = environ.get('TEST_CASE_FIELDS')
        if fields:
            fields = ujson.loads(fields)
        form = self.parse_form()

        self.form = {k: ApiField(v, **fields.get(k, {})) for k, v in form.items()} if form else None

    def parse_form(self):
        form_file = self.environ['wsgi.input']
        content_length = int(self.environ.get('CONTENT_LENGTH', 0))
        form_data = form_file.read(content_length)
        monkey_form_file = io.BytesIO(form_data)
        self.environ['wsgi.input'] = monkey_form_file
        form = parse_any_form(self.environ)
        monkey_form_file.seek(0)
        return form if form else None

    def __call__(self):
        response = self.application(
            self.environ,
            self.start_response_wrapper(self.start_response)
        )
        self.response.load(response)

    def start_response_wrapper(self, start_response):
        def start_response_profiler(status, headers):
            self.response = Response(status, headers)
            return start_response(status, headers)
        return start_response_profiler

    @property
    def url(self):
        return self.environ['PATH_INFO']

    @url.setter
    def url(self, v):
        self.environ['PATH_INFO'] = v

    @property
    def title(self):
        return self.environ['TEST_CASE_TITLE']

    @property
    def verb(self):
        return self.environ['REQUEST_METHOD'].upper()

    @property
    def payload(self):
        return self.environ['wsgi.input']

    @property
    def role(self):
        return self.environ.get('TEST_CASE_ROLE', None)

    @property
    def expected_status(self):
        status = self.environ.get('TEST_CASE_EXPECTED_STATUS', None)
        return int(status) if status else status

    @property
    def description(self):
        return self.environ.get('TEST_CASE_DESCRIPTION', None)

    def to_dict(self):
        return dict(
            title=self.title,
            url=self.url,
            url_parameters=self.url_parameters,
            verb=self.verb,
            query_string=self.query_string,
            response=self.response.dump(),
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


class ApiField(FieldInfo):
    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        import builtins
        t = getattr(builtins, self.type_, str)
        self.value = t(value)
