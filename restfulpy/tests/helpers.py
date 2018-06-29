
import asyncio
import functools
import re
import sys
import unittest
from os.path import join, abspath
from unittest.case import _Outcome
from unittest.util import safe_repr
from urllib.parse import quote, urlencode

import ujson
from nanohttp import settings
from webtest import TestApp

from restfulpy.db import DatabaseManager
from restfulpy.orm import setup_schema, session_factory, create_engine


class RestfulpyTestApp(TestApp):
    _jwt_token = None
    __jwt_header_key__ = 'HTTP_AUTHORIZATION'

    def __init__(self, application, *args, **kwargs):
        self.application = application
        super().__init__(application, *args, **kwargs)

    @property
    def legend_filename(self):
        return join(self.destination_dir, 'legend.md')

    @property
    def jwt_token(self):
        return self._jwt_token

    @jwt_token.setter
    def jwt_token(self, value):
        self._jwt_token = value

        if value is not None:
            self.extra_environ.update({
                self.__jwt_header_key__: value,
            })
        else:
            if self.__jwt_header_key__ in self.extra_environ:
                del self.extra_environ[self.__jwt_header_key__]

    def send_request(self, role, method, url, query=None,
                     url_params=None, params=None, model=None, json=None,
                     content_type=None, **kwargs):
        files = []

        parameters = {}
        if json:
            kwargs.setdefault('content_type', 'application/json')
            kwargs.update(
                params=ujson.dumps(json),
                upload_files=None,
            )

        else:
            kwargs.setdefault('content_type', content_type)
            if params:
                if isinstance(params, dict):
                    parameters = params
                else:
                    for param in params:
                        if param.type_ == 'file':
                            files.append((param.name, param.value))
                        else:
                            parameters[param.name] = param.value

                if parameters:
                    kwargs['params'] = parameters

            if files:
                kwargs['upload_files'] = files

        real_url = (url % url_params) if url_params else url
        real_url = quote(real_url)

        if query:
            real_url = '%s?%s' % (real_url, urlencode(query))

        resp = self._gen_request(
            method.upper(), real_url, expect_errors=True, **kwargs
        )

        kwargs.setdefault('headers', {})
        content_type = kwargs.get('content_type', content_type)
        if content_type:
            kwargs['headers']['Content-Type'] = content_type

        return resp


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
        cls.session = session = session_factory(
            bind=cls.engine,
            expire_on_commit=False
        )
        setup_schema(session)
        session.commit()

    @classmethod
    def mockup(cls):
        pass

    @classmethod
    def drop_database(cls):
        cls.session.close_all()
        cls.engine.dispose()
        with DatabaseManager() as m:
            m.drop_database()

    @classmethod
    def setUpClass(cls):
        cls.configure_app()
        settings.db.url = settings.db.test_url
        cls.prepare_database()
        cls.application.initialize_models()
        cls.wsgi_application = RestfulpyTestApp(cls.application)
        cls.mockup()
        super().setUpClass()

    @classmethod
    def configure_app(cls):
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
    def tearDownClass(cls):
        cls.application.shutdown()
        cls.drop_database()
        super().tearDownClass()

    def _print_statuses_mismatch_error(self, expected_status, response):

        if isinstance(expected_status,int) and response.status_code != expected_status:

            print_ = functools.partial(
                print,
                file=sys.stderr if response.status_code != 200 else sys.stdout
            )

            print_('#' * 80)
            if 'content-type' in response.headers and response.headers[
                'content-type'].startswith('application/json'):
                result = ujson.loads(response.body.decode())
                if isinstance(result, dict) and 'description' in result:
                    print_(result['message'])
                    print_(result['description'])
                else:
                    print_(result)
            else:
                print_(response.body.decode())
            print_('#' * 80)

            if isinstance(expected_status, int):
                self.assertEqual(expected_status, response.status_code)
            else:
                self.assertEqual(expected_status, response.status)

    def _statuses_are_the_same(self, expected, response):
        if isinstance(expected, int):
            return response.status_code == expected

        if isinstance(expected, str):
            return re.match(expected, response.status)

        raise ValueError('Invalid expected status')

    def request(self, role, method, url, query=None, url_params=None,
                params=None, model=None, expected_status=200,
                expected_headers=None, json=None, **kwargs):

        response = self.wsgi_application.send_request(
            role, method, url,
            query=query,
            url_params=url_params,
            params=params,
            model=model,
            json=json,
            **kwargs
        )

        if expected_status and not self._statuses_are_the_same(expected_status, response):
            self._print_statuses_mismatch_error(expected_status, response)

        if expected_headers:
            for k, v in expected_headers.items():
                self.assertIn(k, response.headers)
                self.assertEqual(v, response.headers[k])

        if 'content-type' in response.headers and response.headers['content-type'].startswith('application/json'):
            result = ujson.loads(response.body.decode())
        else:
            result = response.body

        return result, response.headers

    def assertDictContainsSubset(self, dictionary, subset, msg=None):
        """Checks whether dictionary is a superset of subset."""

        missing = []
        mismatched = []
        for key, value in subset.items():
            if key not in dictionary:
                missing.append(key)
            elif value != dictionary[key]:
                mismatched.append(
                    '%s, expected: %s, actual: %s' %
                    (safe_repr(key), safe_repr(value),
                    safe_repr(dictionary[key]))
                )

        if not (missing or mismatched):
            return

        standard_message = ''
        if missing:
            standard_message = 'Missing: %s' % ','.join(
                safe_repr(m) for m in missing)
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
        if getattr(self.__class__, "__unittest_skip__", False) or getattr(
                test_method, "__unittest_skip__", False):
            # If the class or method was skipped.
            try:
                skip_why = (getattr(self.__class__, '__unittest_skip_why__','')
                     or getattr(test_method, '__unittest_skip_why__',''))
                self._addSkip(result, self, skip_why)
            finally:
                result.stopTest(self)
            return
        expecting_failure_method = getattr(test_method, "__unittest_expecting_failure__", False)
        expecting_failure_class = getattr(self, "__unittest_expecting_failure__", False)
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
                msg = self._formatMessage(self.msg, "%s not raised by %s" % (
                expected_exception, func.__name__))
                raise self.failureException(msg)

