import ujson
import asyncio
import unittest
from unittest.util import safe_repr
from unittest.case import _Outcome
from os.path import join, abspath

from nanohttp import settings

from restfulpy.db import DatabaseManager
from restfulpy.orm import setup_schema, session_factory, DBSession, create_engine
from restfulpy.testing.documentation import DocumentaryTestApp


class WebAppTestCase(unittest.TestCase):
    application = None
    session = None
    engine = None

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
    def mockup(cls):
        pass

    @classmethod
    def drop_database(cls):
        cls.session.close_all()
        if cls.session.bind and hasattr(cls.session.bind, 'dispose'):
            DBSession.bind.dispose()
        cls.engine.dispose()

        with DatabaseManager() as m:
            m.drop_database()

    @classmethod
    def setUpClass(cls):
        cls.configure_app()
        settings.db.uri = settings.db.test_uri
        cls.prepare_database()
        cls.application.initialize_models()
        cls.mockup()
        cls.wsgi_app = DocumentaryTestApp(
            abspath(join(settings.api_documents.directory, 'api')),
            cls.application
        )
        super().setUpClass()

    @classmethod
    def configure_app(cls):
        cls.application.configure(force=True)
        settings.merge("""
            messaging:
              default_messenger: restfulpy.testing.MockupMessenger
            logging:
              loggers:
                default:
                  level: critical
            """)

    @classmethod
    def tearDownClass(cls):
        cls.drop_database()
        super().tearDownClass()

    def request(self, role, method, url, query_string=None, url_params=None, params=None, model=None, doc=True,
                expected_status=200, expected_headers=None, json=None, **kwargs):

        resp = self.wsgi_app.send_request(
            role, method, url,
            query_string=query_string,
            url_params=url_params,
            params=params,
            model=model,
            doc=doc,
            json=json,
            **kwargs
        )

        if resp.status_code != expected_status:
            print('#' * 80)
            if 'content-type' in resp.headers and resp.headers['content-type'].startswith('application/json'):
                result = ujson.loads(resp.body.decode())
                print(result['message'])
                print(result['description'])
            else:
                print(resp.body)
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

        return result, resp.headers

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


class AioTestCase(unittest.TestCase):
    # noinspection PyPep8Naming
    def __init__(self, *args, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        super(AioTestCase, self).__init__(*args)

    def _run_method(self, func, *args, **kwargs):
        if asyncio.iscoroutinefunction(func):
            return self.loop.run_until_complete(func(*args, **kwargs))
        else:
            return func(*args, **kwargs)

    def run(self, result=None):
        orig_result = result
        if result is None:
            result = self.defaultTestResult()
            start_test_run = getattr(result, 'startTestRun', None)
            if start_test_run is not None:
                start_test_run()

        result.startTest(self)

        test_method = getattr(self, self._testMethodName)
        if getattr(self.__class__, "__unittest_skip__", False) or getattr(test_method, "__unittest_skip__", False):
            # If the class or method was skipped.
            try:
                skip_why = (getattr(self.__class__, '__unittest_skip_why__', '')
                            or getattr(test_method, '__unittest_skip_why__', ''))
                self._addSkip(result, self, skip_why)
            finally:
                result.stopTest(self)
            return
        expecting_failure_method = getattr(test_method,
                                           "__unittest_expecting_failure__", False)
        expecting_failure_class = getattr(self,
                                          "__unittest_expecting_failure__", False)
        expecting_failure = expecting_failure_class or expecting_failure_method
        outcome = _Outcome(result)
        try:
            self._outcome = outcome

            with outcome.testPartExecutor(self):
                self._run_method(self.setUp)
            if outcome.success:
                outcome.expecting_failure = expecting_failure
                with outcome.testPartExecutor(self, isTest=True):
                    self._run_method(test_method)
                outcome.expecting_failure = False
                with outcome.testPartExecutor(self):
                    self._run_method(self.tearDown)

            self.doCleanups()
            for test, reason in outcome.skipped:
                self._addSkip(result, test, reason)
            self._feedErrorsToResult(result, outcome.errors)
            if outcome.success:
                if expecting_failure:
                    if outcome.expectedFailure:
                        self._addExpectedFailure(result, outcome.expectedFailure)
                    else:
                        self._addUnexpectedSuccess(result)
                else:
                    result.addSuccess(self)
            return result
        finally:
            result.stopTest(self)
            if orig_result is None:
                stop_test_run = getattr(result, 'stopTestRun', None)
                if stop_test_run is not None:
                    stop_test_run()

            # explicitly break reference cycles:
            # outcome.errors -> frame -> outcome -> outcome.errors
            # outcome.expectedFailure -> frame -> outcome -> outcome.expectedFailure
            outcome.errors.clear()
            outcome.expectedFailure = None

            # clear the outcome, no more needed
            self._outcome = None

    # noinspection PyMethodOverriding
    async def assertRaises(self, expected_exception, func, *args, **kwargs):
        try:
            await func(*args, **kwargs)
        except Exception as ex:
            if not isinstance(ex, expected_exception):
                # noinspection PyUnresolvedReferences
                msg = self._formatMessage(self.msg, "%s not raised by %s" % (expected_exception, func.__name__))
                raise self.failureException(msg)
