import copy
import re
import unittest

from nanohttp import context, json, settings

from restfulpy.principal import DummyIdentity
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.validation import validate_form
from restfulpy.controllers import RestController, RootController


class ValidationPatternController(RestController):

    @json
    @validate_form(
        pattern={
            'patternedParam1': re.compile(r'^\d{10}$'),
            'patternedParam2': '^\D{10}$',
            'patternedParam3': re.compile(r'^Exact$'),
        },
        client={
           'pattern': {
               'patternedParam1': re.compile(r'^\d{5}$'),
               'patternedParam2': re.compile(r'^\D{5}$')
           }
        },
        admin={
           'pattern': {
               'patternedParam1': '^\d+$',
               'patternedParam4': re.compile(r'^SuperAdmin$')
           }
        }
    )
    def post(self):
        result = copy.deepcopy(context.form)
        result.update(context.query_string)
        return result


class Root(RootController):
    validation = ValidationPatternController()


class ValidationPatternTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', Root())

    @classmethod
    def configure_app(cls):
        super().configure_app()
        settings.merge("""
            logging:
              loggers:
                default:
                  level: info
            """)

    def test_validation_pattern(self):
        # Test `pattern`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        self.request(
            'All', 'POST', '/validation',
            doc=False,
            params={
                'patternedParam1': '0123456789',
                'patternedParam2': 'abcdeFGHIJ',
                'patternedParam3': 'Exact'
            }
        )

        self.request(
            'All', 'POST', '/validation',
            doc=False,
            params={'patternedParam1': '12345'},
            expected_status=400
        )

        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()
        self.request(
            'Client', 'POST', '/validation',
            doc=False,
            params={
                'patternedParam1': '12345',
                'patternedParam2': 'ABCDE',
                'patternedParam3': 'Exact',
                'patternedParam4': 'anything'
            }
        )

        self.request(
            'Client', 'POST', '/validation',
            doc=False,
            params={'patternedParam1': '1'},
            expected_status=400
        )

        # -----------------------------
        # role -> Admin
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()
        self.request(
            'Admin', 'POST', '/validation',
            doc=False,
            params={
                'patternedParam1': '1',
                'patternedParam2': 'ABCDEFGHIJ',
                'patternedParam4': 'SuperAdmin'
            }
        )

        self.request(
            'Admin', 'POST', '/validation',
            doc=False,
            params={'patternedParam4': 'anything'},
            expected_status=400
        )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
