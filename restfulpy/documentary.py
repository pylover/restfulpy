from urllib.parse import parse_qs
from os.path import join, abspath
import unittest
import re

import yaml
import webtest
from nanohttp import settings

from restfulpy.db import DatabaseManager
from restfulpy.orm import setup_schema, session_factory, create_engine

URL_PARAMETER_PATTERN = re.compile('/(?P<key>\w+):\s?(?P<value>\w+)')


class Response:

    def __init__(self, status=None, headers=None):
        self.status = status
        self.headers = headers or []
        self.buffer = []

    def load(self, wsgi_response):
        for chunk in wsgi_response:
            self.buffer.append(chunk)
        return self.buffer

    def dump(self):
        return dict(
            status=self.status,
            headers=self.headers,
            body=b''.join(self.buffer)
        )


class ApiCall:
    response = None

    def __init__(self, application, environ, start_response):
        self.application = application
        self.environ = environ
        self.start_response = start_response

        # noinspection PyTypeChecker
        self.url_parameters = dict()
        url = self.url
        for k, v in URL_PARAMETER_PATTERN.findall(self.url):
            self.url_parameters[k] = v
            url = re.sub(f'{k}:\s?', '', url)
        self.url = url

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
    def query_string(self):
        return {k: v[0] if len(v) == 1 else v for k, v in parse_qs(
            self.environ['QUERY_STRING'],
            keep_blank_values=True,
            strict_parsing=False
        ).items()}

    def to_dict(self):
        return dict(
            title=self.title,
            url=self.url,
            url_parameters=self.url_parameters,
            verb=self.verb,
            query_string=self.query_string,
            response=self.response.dump(),
        )

    def dump(self, file):
        yaml.dump(self.to_dict(), file)

    def save(self, directory):
        with open(join(directory, self.filename), '-w') as f:
            self.dump(f)

    @property
    def filename(self):
        url = self.url
        return f'{url}'


class AbstractDocumentaryMiddleware:

    def __init__(self, application):
        self.application = application

    def on_call_done(self, call):
        raise NotImplementedError()

    def __call__(self, environ, start_response):
        call = ApiCall(self.application, environ, start_response)
        call()
        self.on_call_done(call)
        for i in call.response.buffer:
            yield i


class FileDocumentaryMiddleware(AbstractDocumentaryMiddleware):

    def __init__(self, application, directory=None):
        super().__init__(application)
        self.directory = directory

    def on_call_done(self, call):
        call.save(self.directory)


class WSGIDocumentaryTestCase(unittest.TestCase):
    application = None
    api_client = None

    @staticmethod
    def application_factory():
        raise NotImplementedError()

    @staticmethod
    def documentary_middleware_factory(app):
        return FileDocumentaryMiddleware(app, abspath(join(settings.api_documents.directory, 'source')))

    @classmethod
    def setUpClass(cls):
        cls.application = cls.application_factory()
        cls.api_client = webtest.TestApp(cls.documentary_middleware_factory(cls.application))
        super().setUpClass()

    def call(self, title, verb, url, *, arguments=None, environ=None, description=None, **kwargs):
        environ = environ or {}
        environ['TEST_CASE_TITLE'] = title

        if description:
            environ['TEST_CASE_DESCRIPTION'] = description

        if arguments:
            environ['TEST_CASE_ARGUMENT_NAMES'] = arguments

        return self.api_client._gen_request(
            verb.upper(), url,
            expect_errors=True,
            extra_environ=environ,
            **kwargs
        )


# noinspection PyAbstractClass
class RestfulpyApplicationTestCase(WSGIDocumentaryTestCase):
    session = None
    engine = None

    @classmethod
    def configure_application(cls):
        cls.application.configure(force=True, context=dict(unittest=True))
        settings.merge("""
            messaging:
              default_messenger: restfulpy.testing.MockupMessenger
            logging:
              loggers:
                default:
                  level: critical
        """)

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
        if cls.session.bind and hasattr(cls.session.bind, 'dispose'):
            cls.session.bind.dispose()
        cls.engine.dispose()

        with DatabaseManager() as m:
            m.drop_database()

    @classmethod
    def mockup(cls):
        pass

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configure_application()
        settings.db.url = settings.db.test_url
        cls.prepare_database()
        cls.application.initialize_models()
        cls.mockup()

    @classmethod
    def tearDownClass(cls):
        cls.drop_database()
        super().tearDownClass()

