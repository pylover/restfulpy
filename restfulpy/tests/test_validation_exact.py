import copy
import unittest

from nanohttp import context, json, settings

from restfulpy.principal import DummyIdentity
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.validation import validate_form
from restfulpy.controllers import RestController, RootController


class ValidationController(RestController):

    @json
    @validate_form(exact=['exactParamForAll'],
                   client={'exact': ['exactParamForClient']},
                   admin={'exact': ['exactParamForAdmin']})
    def post(self):
        result = copy.deepcopy(context.form)
        result.update(context.query_string)
        return result


class Root(RootController):
    validation = ValidationController()


class ValidationExactTestCase(WebAppTestCase):
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

    def test_validation_exact(self):
        # Test `exact`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        result, ___ = self.request('All', 'POST', '/validation', doc=False, params={'exactParamForAll': 'param'})
        self.request('All', 'POST', '/validation', doc=False, expected_status=400)
        self.request(
            'All', 'POST', '/validation', doc=False,
            params={
                'exactParamForAll': 'param',
                'exactParamForCustom': 'param',
            },
            expected_status=400
        )
        self.request('All', 'POST', '/validation', doc=False, params={'exactParamForCustom': 'param'},
                     expected_status=400)
        self.assertIn('exactParamForAll', result)
        self.request(
            'All', 'POST', '/validation', doc=False,
            params={
                'exactParamForAll': 'param',
                'exactParamForClient': 'param',
            },
            expected_status=400
        )
        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()

        result, ___ = self.request(
            'Client', 'POST', '/validation', doc=False,
            params={
                'exactParamForAll': 'param',
                'exactParamForClient': 'param',
            }
        )
        self.assertIn('exactParamForClient', result)
        self.assertIn('exactParamForAll', result)

        self.request(
            'Client', 'POST', '/validation', doc=False,
            params={
                'exactParamForAll': 'param',
                'exactParamForClient': 'param',
                'exactParamForAdmin': 'param',
            },
            expected_status=400
        )

        # -----------------------------
        # role -> Admin
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()

        result, ___ = self.request('Admin', 'POST', '/validation', doc=False, params={
            'exactParamForAll': 'param',
            'exactParamForAdmin': 'param',
        })
        self.assertIn('exactParamForAdmin', result)
        self.assertIn('exactParamForAll', result)

        self.request('Admin', 'POST', '/validation', doc=False, params={
            'exactParamForAll': 'param',
            'exactParamForClient': 'param',
            'exactParamForAdmin': 'param',
        }, expected_status=400)

        # ------------------------------------------------------------

        # Test query string
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()
        result, ___ = self.request(
            'Admin', 'POST', '/validation', doc=False,
            query_string={
                'exactParamForAll': 'param',
            },
            params={
                'exactParamForAdmin': 'param',
            }
        )
        self.assertIn('exactParamForAdmin', result)
        self.assertIn('exactParamForAll', result)

        self.request(
            'Admin', 'POST', '/validation', doc=False,
            query_string={
                'exactParamForAll': 'param',
                'exactParamForClient': 'param',
            },
            params={'exactParamForAdmin': 'param'}, expected_status=400
        )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
