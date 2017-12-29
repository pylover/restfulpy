import unittest
from urllib.parse import urlencode
from os import path

import webtest
from nanohttp import settings
import ujson

from restfulpy.db import DatabaseManager
from restfulpy.orm import setup_schema, session_factory, create_engine
from restfulpy.application import Application


class WSGIDocumentaryTestCase(unittest.TestCase):
    application = None
    api_client = None
    controller_factory = None
    application_factory = None
    fields = None

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

        if self.fields:
            environ['TEST_CASE_FIELDS'] = ujson.dumps({n: f.to_dict() for n, f in self.fields.items()})

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
