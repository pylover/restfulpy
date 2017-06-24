import copy
import unittest

from nanohttp import context, json, settings

from restfulpy.principal import DummyIdentity
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.validation import validate_form
from restfulpy.controllers import RestController, RootController


class ValidationWhitelistController(RestController):

    @json
    @validate_form(whitelist=['whitelistParamForAll'],
                   client={'whitelist': ['whitelistParamForClient']},
                   admin={'whitelist': ['whitelistParamForAdmin']})
    def post(self):
        result = copy.deepcopy(context.form)
        result.update(context.query_string)
        return result


class Root(RootController):
    validation = ValidationWhitelistController()


class ValidationWhitelistTestCase(WebAppTestCase):
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

    def test_validation_whitelist(self):
        # Test `whitelist`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        result, ___ = self.request('All', 'POST', '/validation', doc=False,
                                   params={'whitelistParamForAll': 'param'})
        self.assertIn('whitelistParamForAll', result)
        self.request('All', 'POST', '/validation', doc=False)
        self.request(
            'All', 'POST', '/validation', doc=False,
            params={
                'whitelistParamForAll': 'param',
                'customParam': 'param'
            },
            expected_status=400
        )
        self.request('All', 'POST', '/validation', doc=False, params={'customParam': 'param'},
                     expected_status=400)
        self.request('All', 'POST', '/validation', doc=False, params={'whitelistParamForClient': 'param', },
                     expected_status=400)
        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()

        result, ___ = self.request('Client', 'POST', '/validation', doc=False,
                                   params={'whitelistParamForAll': 'param'})
        self.assertIn('whitelistParamForAll', result)

        result, ___ = self.request('Client', 'POST', '/validation', doc=False,
                                   params={'whitelistParamForClient': 'param'})
        self.assertIn('whitelistParamForClient', result)

        result, ___ = self.request(
            'Client', 'POST', '/validation', doc=False,
            params={
                'whitelistParamForAll': 'param',
                'whitelistParamForClient': 'param',
            }
        )
        self.assertIn('whitelistParamForAll', result)
        self.assertIn('whitelistParamForClient', result)

        self.request('Client', 'POST', '/validation', doc=False)

        self.request(
            'Client', 'POST', '/validation', doc=False,
            params={
                'whitelistParamForAll': 'param',
                'customParam': 'param',
            },
            expected_status=400
        )

        self.request(
            'Client', 'POST', '/validation', doc=False,
            params={
                'customParam': 'param',
            },
            expected_status=400
        )

        self.request(
            'Client', 'POST', '/validation', doc=False,
            params={
                'whitelistParamForAdmin': 'param',
            },
            expected_status=400
        )

        # -----------------------------
        # role -> Admin
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()

        result, ___ = self.request('Admin', 'POST', '/validation', doc=False,
                                   params={'whitelistParamForAll': 'param'})
        self.assertIn('whitelistParamForAll', result)

        result, ___ = self.request('Admin', 'POST', '/validation', doc=False,
                                   params={'whitelistParamForAdmin': 'param'})
        self.assertIn('whitelistParamForAdmin', result)

        result, ___ = self.request(
            'Admin', 'POST', '/validation', doc=False,
            params={
                'whitelistParamForAll': 'param',
                'whitelistParamForAdmin': 'param',
            }
        )
        self.assertIn('whitelistParamForAll', result)
        self.assertIn('whitelistParamForAdmin', result)

        self.request('Admin', 'POST', '/validation', doc=False)

        self.request(
            'Admin', 'POST', '/validation', doc=False,
            params={
                'whitelistParamForAll': 'param',
                'customParam': 'param',
            },
            expected_status=400
        )

        self.request('Admin', 'POST', '/validation', doc=False, params={
            'customParam': 'param',
        }, expected_status=400)

        self.request(
            'Admin', 'POST', '/validation', doc=False,
            params={
                'whitelistParamForAll': 'param',
                'whitelistParamForAdmin': 'param',
                'whitelistParamForClient': 'param',
            },
            expected_status=400
        )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
