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
    @validate_form(deny=['deniedParamForAll'],
                   client={'deny': ['deniedParamForClient']},
                   admin={'deny': ['deniedParamForAdmin']})
    def test_deny(self):
        result = copy.deepcopy(context.form)
        result.update(context.query_string)
        return result

    @json
    @validate_form(exclude=['excludedParamForAll'],
                   client={'exclude': ['excludedParamForClient']},
                   admin={'exclude': ['excludedParamForAdmin']})
    def test_exclude(self):
        result = copy.deepcopy(context.form)
        result.update(context.query_string)
        return result

    @json
    @validate_form(
        filter_=['filteredParamForAll'],
        client=dict(filter_=['filteredParamForClient']),
        admin=dict(filter_=['filteredParamForAdmin'])
    )
    def test_filter(self):
        result = copy.deepcopy(context.form)
        result.update(context.query_string)
        return result

    @json
    @validate_form(only=['onlyParamForAll'],
                   client={'only': ['onlyParamForClient']},
                   admin={'only': ['onlyParamForAdmin']})
    def test_only(self):
        result = copy.deepcopy(context.form)
        result.update(context.query_string)
        return result


class Root(RootController):
    validation = ValidationController()


class ValidationTestCase(WebAppTestCase):
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

    def test_validation1(self):
        # Test `deny`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        self.request('All', 'TEST_DENY', '/validation')
        self.request('All', 'TEST_DENY', '/validation', params={'customParam': 'param'})
        self.request('All', 'TEST_DENY', '/validation', params={'deniedParamForAll': 'param'}, expected_status=400)
        self.request('All', 'TEST_DENY', '/validation', params={'deniedParamForClient': 'param'})
        self.request('All', 'TEST_DENY', '/validation', params={'deniedParamForAdmin': 'param'})
        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()
        self.request('Client', 'TEST_DENY', '/validation')
        self.request('Client', 'TEST_DENY', '/validation', params={'customParam': 'param'})
        self.request('Client', 'TEST_DENY', '/validation', params={'deniedParamForAll': 'param'}, expected_status=400)
        self.request(
            'Client', 'TEST_DENY', '/validation',
            params={'deniedParamForClient': 'param'},
            expected_status=400
        )
        self.request('Client', 'TEST_DENY', '/validation', params={
            'deniedParamForAdmin': 'param'
        })
        # -----------------------------
        # role -> Admin
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()
        self.request('Admin', 'TEST_DENY', '/validation')
        self.request('Admin', 'TEST_DENY', '/validation', params={
            'customParam': 'param'
        })
        self.request('Admin', 'TEST_DENY', '/validation', params={
            'deniedParamForAll': 'param'
        }, expected_status=400)
        self.request('Admin', 'TEST_DENY', '/validation', params={
            'deniedParamForClient': 'param'
        })
        self.request('Admin', 'TEST_DENY', '/validation', params={
            'deniedParamForAdmin': 'param'
        }, expected_status=400)

        # ------------------------------------------------------------

        # Test `exclude`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        result, ___ = self.request('All', 'TEST_EXCLUDE', '/validation', params={
            'customParam': 'param',
            'excludedParamForAll': 'param',
            'excludedParamForClient': 'param',
            'excludedParamForAdmin': 'param',
        })
        self.assertIn('customParam', result)
        self.assertIn('excludedParamForClient', result)
        self.assertIn('excludedParamForAdmin', result)
        self.assertNotIn('excludedParamForAll', result)
        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()
        result, ___ = self.request('Client', 'TEST_EXCLUDE', '/validation', params={
            'customParam': 'param',
            'excludedParamForAll': 'param',
            'excludedParamForClient': 'param',
            'excludedParamForAdmin': 'param',
        })
        self.assertIn('customParam', result)
        self.assertNotIn('excludedParamForClient', result)
        self.assertIn('excludedParamForAdmin', result)
        self.assertNotIn('excludedParamForAll', result)
        # -----------------------------
        # role -> Admin
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()
        result, ___ = self.request('Admin', 'TEST_EXCLUDE', '/validation', params={
            'customParam': 'param',
            'excludedParamForAll': 'param',
            'excludedParamForClient': 'param',
            'excludedParamForAdmin': 'param',
        })
        self.assertIn('customParam', result)
        self.assertIn('excludedParamForClient', result)
        self.assertNotIn('excludedParamForAdmin', result)
        self.assertNotIn('excludedParamForAll', result)

        # ------------------------------------------------------------

        # Test `filter`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        result, ___ = self.request('All', 'TEST_FILTER', '/validation', params={
            'customParam': 'param',
            'filteredParamForAll': 'param',
            'filteredParamForClient': 'param',
            'filteredParamForAdmin': 'param',
        })
        self.assertNotIn('customParam', result)
        self.assertNotIn('filteredParamForClient', result)
        self.assertNotIn('filteredParamForAdmin', result)
        self.assertIn('filteredParamForAll', result)
        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()
        result, ___ = self.request(
            'Client', 'TEST_FILTER', '/validation',
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
        result, ___ = self.request('Admin', 'TEST_FILTER', '/validation', params={
            'customParam': 'param',
            'filteredParamForAll': 'param',
            'filteredParamForClient': 'param',
            'filteredParamForAdmin': 'param',
        })
        self.assertNotIn('customParam', result)
        self.assertNotIn('filteredParamForClient', result)
        self.assertIn('filteredParamForAdmin', result)
        self.assertIn('filteredParamForAll', result)

        # ------------------------------------------------------------

        # Test `only`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        result, ___ = self.request('All', 'TEST_ONLY', '/validation', params={
            'onlyParamForAll': 'param',
        })
        self.request('All', 'TEST_ONLY', '/validation', params={
        }, expected_status=400)
        self.request('All', 'TEST_ONLY', '/validation', params={
            'onlyParamForAll': 'param',
            'onlyParamForCustom': 'param',
        }, expected_status=400)
        self.request('All', 'TEST_ONLY', '/validation', params={
            'onlyParamForCustom': 'param',
        }, expected_status=400)
        self.assertIn('onlyParamForAll', result)
        self.request('All', 'TEST_ONLY', '/validation', params={
            'onlyParamForAll': 'param',
            'onlyParamForClient': 'param',
        }, expected_status=400)
        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()
        result, ___ = self.request('Client', 'TEST_ONLY', '/validation', params={
            'onlyParamForAll': 'param',
            'onlyParamForClient': 'param',
        })
        self.assertIn('onlyParamForClient', result)
        self.assertIn('onlyParamForAll', result)
        self.request('Client', 'TEST_ONLY', '/validation', params={
            'onlyParamForAll': 'param',
            'onlyParamForClient': 'param',
            'onlyParamForAdmin': 'param',
        }, expected_status=400)
        # -----------------------------
        # role -> Admin
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()
        result, ___ = self.request('Admin', 'TEST_ONLY', '/validation', params={
            'onlyParamForAll': 'param',
            'onlyParamForAdmin': 'param',
        })
        self.assertIn('onlyParamForAdmin', result)
        self.assertIn('onlyParamForAll', result)
        self.request('Admin', 'TEST_ONLY', '/validation', params={
            'onlyParamForAll': 'param',
            'onlyParamForClient': 'param',
            'onlyParamForAdmin': 'param',
        }, expected_status=400)

        # ------------------------------------------------------------

        # Test query string
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()
        result, ___ = self.request('Admin', 'TEST_ONLY', '/validation', query_string={
            'onlyParamForAll': 'param',
        }, params={
            'onlyParamForAdmin': 'param',
        })
        self.assertIn('onlyParamForAdmin', result)
        self.assertIn('onlyParamForAll', result)
        self.request('Admin', 'TEST_ONLY', '/validation', query_string={
            'onlyParamForAll': 'param',
            'onlyParamForClient': 'param',
        }, params={
            'onlyParamForAdmin': 'param',
        }, expected_status=400)


if __name__ == '__main__':
    unittest.main()
