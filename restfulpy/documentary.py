import io
import re
import unittest
import collections
from urllib.parse import parse_qs, urlencode
from os import path, makedirs

import ujson
import yaml
import webtest
from nanohttp import settings
from nanohttp.helpers import parse_any_form

from restfulpy.db import DatabaseManager
from restfulpy.orm import setup_schema, session_factory, create_engine
from restfulpy.application import Application


URL_PARAMETER_PATTERN = re.compile('/(?P<key>\w+):\s?(?P<value>\w+)')
CONTENT_TYPE_PATTERN = re.compile('(\w+/\w+)(?:;\s?charset=(.+))?')


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

        self.form = self.parse_form()

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
            form=self.form,
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


class AbstractDocumentaryMiddleware:

    def __init__(self, application, history_maxlen=50):
        self.application = application
        self.call_history = collections.deque(maxlen=history_maxlen)

    def on_call_done(self, call):
        raise NotImplementedError()

    def __call__(self, environ, start_response):
        call = ApiCall(self.application, environ, start_response)
        call()
        self.call_history.append(call)
        self.on_call_done(call)
        for i in call.response.buffer:
            yield i


class FileDocumentaryMiddleware(AbstractDocumentaryMiddleware):

    def __init__(self, application, directory=None):
        super().__init__(application)
        if not path.exists(directory):
            makedirs(directory, exist_ok=True)
        self.directory = directory

    def on_call_done(self, call):
        call.save(self.directory)


class WSGIDocumentaryTestCase(unittest.TestCase):
    application = None
    api_client = None
    controller_factory = None
    application_factory = None

    @staticmethod
    def documentary_middleware_factory(app):
        return FileDocumentaryMiddleware(app, path.abspath(path.join(settings.api_documents.directory, 'source')))

    @classmethod
    def application_factory(cls):
        if cls.controller_factory:
            app = Application(f'{cls.__name__}Application', cls.controller_factory())
            app.configure(force=True)
            return app
        else:
            raise ValueError('One of controller_factory and or application_factory must be provided.')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.application = cls.application_factory()
        cls.api_client = webtest.TestApp(cls.documentary_middleware_factory(cls.application))

    def call(self, title, verb, url, *, query=None, environ=None, description=None, form=None, role=None, status=200,
             **kwargs):
        environ = environ or {}
        environ['TEST_CASE_TITLE'] = title

        if description:
            environ['TEST_CASE_DESCRIPTION'] = description

        if role:
            environ['TEST_CASE_ROLE'] = role

        if status:
            environ['TEST_CASE_EXPECTED_STATUS'] = str(status)

        if query:
            if isinstance(query, str):
                url += f'?{query}'
            else:
                url = f'{url}?{urlencode(query, doseq=True)}'

        if form:
            kwargs['params'] = form

        response = self.api_client._gen_request(
            verb.upper(), url,
            expect_errors=status is not None,
            extra_environ=environ,
            **kwargs
        )
        if status:
            self.assertEqual(status, response.status_code)
        return response


# noinspection PyAbstractClass
class RestfulpyApplicationTestCase(WSGIDocumentaryTestCase):
    session = None
    engine = None

    @classmethod
    def application_factory(cls):
        app = super().application_factory()
        app.configure(force=True, context=dict(unittest=True))
        settings.merge('''
            messaging:
              default_messenger: restfulpy.testing.MockupMessenger
            logging:
              loggers:
                default:
                  level: critical
        ''')
        settings.db.url = settings.db.test_url
        return app

    @classmethod
    def prepare_database(cls):
        with DatabaseManager() as m:
            m.drop_database()
            m.create_database()

        cls.engine = create_engine()
        cls.session = session = session_factory(bind=cls.engine, expire_on_commit=False)
        setup_schema(session)
        session.commit()

    @classmethod
    def drop_database(cls):
        cls.session.close_all()
        cls.engine.dispose()
        with DatabaseManager() as m:
            m.drop_database()

    @classmethod
    def mockup(cls):
        pass

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prepare_database()
        cls.application.initialize_models()
        cls.mockup()

    @classmethod
    def tearDownClass(cls):
        cls.application.shutdown()
        cls.drop_database()
        super().tearDownClass()
