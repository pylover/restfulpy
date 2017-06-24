import copy
import unittest

from nanohttp import context, json, settings

from restfulpy.principal import DummyIdentity
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.validation import validate_form
from restfulpy.controllers import RestController, RootController


class ValidationExcludeController(RestController):

    @json
    @validate_form(exclude=['excludedParamForAll'],
                   client={'exclude': ['excludedParamForClient']},
                   admin={'exclude': ['excludedParamForAdmin']})
    def post(self):
        result = copy.deepcopy(context.form)
        result.update(context.query_string)
        return result


class Root(RootController):
    validation = ValidationExcludeController()


class ValidationExcludeTestCase(WebAppTestCase):
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

    def test_validation_exclude(self):
        # Test `exclude`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        result, ___ = self.request(
            'All', 'POST', '/validation', doc=False,
            params={
                'customParam': 'param',
                'excludedParamForAll': 'param',
                'excludedParamForClient': 'param',
                'excludedParamForAdmin': 'param',
            }
        )
        self.assertIn('customParam', result)
        self.assertIn('excludedParamForClient', result)
        self.assertIn('excludedParamForAdmin', result)
        self.assertNotIn('excludedParamForAll', result)
        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()
        result, ___ = self.request(
            'Client', 'POST', '/validation', doc=False,
            params={
                'customParam': 'param',
                'excludedParamForAll': 'param',
                'excludedParamForClient': 'param',
                'excludedParamForAdmin': 'param',
            }
        )
        self.assertIn('customParam', result)
        self.assertNotIn('excludedParamForClient', result)
        self.assertIn('excludedParamForAdmin', result)
        self.assertNotIn('excludedParamForAll', result)
        # -----------------------------
        # role -> Admin
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()
        result, ___ = self.request(
            'Admin', 'POST', '/validation', doc=False,
            params={
                'customParam': 'param',
                'excludedParamForAll': 'param',
                'excludedParamForClient': 'param',
                'excludedParamForAdmin': 'param',
            }
        )
        self.assertIn('customParam', result)
        self.assertIn('excludedParamForClient', result)
        self.assertNotIn('excludedParamForAdmin', result)
        self.assertNotIn('excludedParamForAll', result)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
