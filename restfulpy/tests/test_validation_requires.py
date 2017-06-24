import copy
import unittest

from nanohttp import context, json, settings

from restfulpy.principal import DummyIdentity
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.validation import validate_form
from restfulpy.controllers import RestController, RootController


class ValidationRequiresController(RestController):

    @json
    @validate_form(requires=['requiresParamForAll'],
                   client={'requires': ['requiresParamForClient']},
                   admin={'requires': ['requiresParamForAdmin']})
    def post(self):
        result = copy.deepcopy(context.form)
        result.update(context.query_string)
        return result


class Root(RootController):
    validation = ValidationRequiresController()


class ValidationRequiresTestCase(WebAppTestCase):
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

    def test_validation_requires(self):
        # Test `requires`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()

        result, ___ = self.request('All', 'POST', '/validation', doc=False,
                                   params={'requiresParamForAll': 'param'})
        self.assertIn('requiresParamForAll', result)

        result, ___ = self.request(
            'All', 'POST', '/validation', doc=False,
            params={
                'customParam': 'param',
                'requiresParamForAll': 'param',
            }
        )
        self.assertIn('customParam', result)
        self.assertIn('requiresParamForAll', result)

        self.request('All', 'POST', '/validation', doc=False, expected_status=400)

        self.request('All', 'POST', '/validation', doc=False, params={'customParam': 'param'},
                     expected_status=400)

        self.request('All', 'POST', '/validation', doc=False, params={'requiresParamForClient': 'param'},
                     expected_status=400)

        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()
        result, ___ = self.request(
            'Client', 'POST', '/validation', doc=False,
            params={
                'requiresParamForAll': 'param',
                'requiresParamForClient': 'param',
            }
        )
        self.assertIn('requiresParamForAll', result)
        self.assertIn('requiresParamForClient', result)

        result, ___ = self.request(
            'Client', 'POST', '/validation', doc=False,
            params={
                'customParam': 'param',
                'requiresParamForAll': 'param',
                'requiresParamForClient': 'param',
            }
        )
        self.assertIn('customParam', result)
        self.assertIn('requiresParamForAll', result)
        self.assertIn('requiresParamForClient', result)

        self.request('Client', 'POST', '/validation', doc=False, expected_status=400)

        self.request('Client', 'POST', '/validation', doc=False, params={'customParam': 'param'},
                     expected_status=400)

        self.request('Client', 'POST', '/validation', doc=False, params={'requiresParamForAll': 'param'},
                     expected_status=400)

        self.request('Client', 'POST', '/validation', doc=False, params={
            'requiresParamForClient':
                'param',
        }, expected_status=400)
        # -----------------------------
        # role -> Admin
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()
        result, ___ = self.request('Admin', 'POST', '/validation', doc=False, params={
            'requiresParamForAll': 'param',
            'requiresParamForAdmin': 'param',
        })
        self.assertIn('requiresParamForAll', result)
        self.assertIn('requiresParamForAdmin', result)
        result, ___ = self.request(
            'Admin', 'POST', '/validation', doc=False,
            params={
                'customParam': 'param',
                'requiresParamForAll': 'param',
                'requiresParamForAdmin': 'param',
            }
        )
        self.assertIn('customParam', result)
        self.assertIn('requiresParamForAll', result)
        self.assertIn('requiresParamForAdmin', result)

        self.request('Admin', 'POST', '/validation', doc=False, expected_status=400)

        self.request('Admin', 'POST', '/validation', doc=False, params={'customParam': 'param'},
                     expected_status=400)

        self.request(
            'Admin', 'POST', '/validation', doc=False,
            params={
                'requiresParamForAll': 'param',
                'requiresParamForClient': 'param',
            },
            expected_status=400
        )

        self.request('Admin', 'POST', '/validation', doc=False, params={'requiresParamForAdmin': 'param'},
                     expected_status=400)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
