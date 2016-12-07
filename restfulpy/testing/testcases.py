
import ujson
import unittest
from unittest.util import safe_repr
from os.path import join, abspath

from nanohttp import settings

from restfulpy.db import DatabaseManager
from restfulpy.orm import setup_schema, create_engine, session_factory, DBSession
from restfulpy.testing.documentation import DocumentaryTestApp


class WebAppTestCase(unittest.TestCase):
    application = None

    @classmethod
    def prepare_database(cls):
        with DatabaseManager() as m:
            m.drop_database()
            m.create_database()

        engine = create_engine()
        session = session_factory(bind=engine)
        setup_schema(session)
        session.commit()
        session.close_all()
        engine.dispose()

    @classmethod
    def drop_database(cls):
        DBSession.close_all()
        if DBSession.bind and hasattr(DBSession.bind, 'dispose'):
            DBSession.bind.dispose()
        with DatabaseManager() as m:
            m.drop_database()

    @classmethod
    def setUpClass(cls):
        cls.application.configure(force=True)
        settings.merge("""
        messaging:
            default_messenger: restfulpy.testing.MockupMessenger
        """)
        settings.db.uri = settings.db.test_uri
        cls.prepare_database()
        cls.application.initialize_models()
        cls.application.insert_basedata()
        cls.application.insert_mockup()
        cls.wsgi_app = DocumentaryTestApp(
            abspath(join(settings.api_documents.directory, 'api')),
            cls.application
        )

    @classmethod
    def tearDownClass(cls):
        cls.drop_database()

    def request(self, role, method, url, query_string=None, url_params=None, params=None, model=None, doc=True,
                expected_status=200, expected_headers=None, **kwargs):
        resp = self.wsgi_app.send_request(role, method, url, query_string=query_string, url_params=url_params,
                                          params=params, model=model, doc=doc, **kwargs)

        if resp.status_code != expected_status:
            print('#' * 80)
            print(resp.text)
            print('#' * 80)

        self.assertEqual(resp.status_code, expected_status)

        if expected_headers:
            for k, v in expected_headers.items():
                self.assertIn(k, resp.headers)
                self.assertEqual(v, resp.headers[k])

        if 'content-type' in resp.headers and resp.headers['content-type'].startswith('application/json'):
            result = ujson.loads(resp.body.decode())
        else:
            result = resp.body

        return result, None

    def assertDictContainsSubset(self, dictionary, subset, msg=None):
        """Checks whether dictionary is a superset of subset."""

        missing = []
        mismatched = []
        for key, value in subset.items():
            if key not in dictionary:
                missing.append(key)
            elif value != dictionary[key]:
                mismatched.append('%s, expected: %s, actual: %s' %
                                  (safe_repr(key), safe_repr(value),
                                   safe_repr(dictionary[key])))

        if not (missing or mismatched):
            return

        standard_message = ''
        if missing:
            standard_message = 'Missing: %s' % ','.join(safe_repr(m) for m in missing)
        if mismatched:
            if standard_message:
                standard_message += '; '
            standard_message += 'Mismatched values: %s' % ','.join(mismatched)

        self.fail(self._formatMessage(msg, standard_message))


class ModelRestCrudTestCase(WebAppTestCase):
    __model__ = None

    def request(self, *args, model=None, **kwargs):
        return super(ModelRestCrudTestCase, self).request(
            *args,
            model=self.__model__,
            **kwargs
        )
