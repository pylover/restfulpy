import copy
import unittest

from nanohttp import context, json, settings

from restfulpy.principal import DummyIdentity
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.validation import validate_form
from restfulpy.controllers import RestController, RootController


class ValidationFilterController(RestController):

    @json
    @validate_form(
        filter_=['filteredParamForAll'],
        client=dict(filter_=['filteredParamForClient']),
        admin=dict(filter_=['filteredParamForAdmin'])
    )
    def post(self):
        result = copy.deepcopy(context.form)
        result.update(context.query_string)
        return result


class Root(RootController):
    validation = ValidationFilterController()


class ValidationFilterTestCase(WebAppTestCase):
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

    def test_validation_filter(self):
        # Test `filter`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        result, ___ = self.request(
            'All', 'POST', '/validation', doc=False,
            params={
                'customParam': 'param',
                'filteredParamForAll': 'param',
                'filteredParamForClient': 'param',
                'filteredParamForAdmin': 'param',
            }
        )
        self.assertNotIn('customParam', result)
        self.assertNotIn('filteredParamForClient', result)
        self.assertNotIn('filteredParamForAdmin', result)
        self.assertIn('filteredParamForAll', result)
        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()
        result, ___ = self.request(
            'Client', 'POST', '/validation', doc=False,
            params={
                'customParam': 'param',
                'filteredParamForAll': 'param',
                'filteredParamForClient': 'param',
                'filteredParamForAdmin': 'param',
            }
        )
        self.assertNotIn('customParam', result)
        self.assertIn('filteredParamForClient', result)
        self.assertNotIn('filteredParamForAdmin', result)
        self.assertIn('filteredParamForAll', result)
        # -----------------------------
        # role -> Admin
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()
        result, ___ = self.request(
            'Admin', 'POST', '/validation', doc=False,
            params={
                'customParam': 'param',
                'filteredParamForAll': 'param',
                'filteredParamForClient': 'param',
                'filteredParamForAdmin': 'param',
            }
        )
        self.assertNotIn('customParam', result)
        self.assertNotIn('filteredParamForClient', result)
        self.assertIn('filteredParamForAdmin', result)
        self.assertIn('filteredParamForAll', result)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
