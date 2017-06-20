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
    @validate_form(blacklist=['blacklistParamForAll'],
                   client={'blacklist': ['blacklistParamForClient']},
                   admin={'blacklist': ['blacklistParamForAdmin']})
    def test_blacklist(self):
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
    @validate_form(whitelist=['whitelistParamForAll'],
                   client={'whitelist': ['whitelistParamForClient']},
                   admin={'whitelist': ['whitelistParamForAdmin']})
    def test_whitelist(self):
        result = copy.deepcopy(context.form)
        result.update(context.query_string)
        return result

    @json
    @validate_form(requires=['requiresParamForAll'],
                   client={'requires': ['requiresParamForClient']},
                   admin={'requires': ['requiresParamForAdmin']})
    def test_requires(self):
        result = copy.deepcopy(context.form)
        result.update(context.query_string)
        return result

    @json
    @validate_form(exact=['exactParamForAll'],
                   client={'exact': ['exactParamForClient']},
                   admin={'exact': ['exactParamForAdmin']})
    def test_exact(self):
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

    def test_validation_blacklist(self):
        # Test `blacklist`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        self.request('All', 'TEST_BLACKLIST', '/validation', doc=False)
        self.request('All', 'TEST_BLACKLIST', '/validation', doc=False, params={'customParam': 'param'})
        self.request('All', 'TEST_BLACKLIST', '/validation', doc=False, params={'blacklistParamForAll': 'param'},
                     expected_status=400)
        self.request('All', 'TEST_BLACKLIST', '/validation', doc=False, params={'blacklistParamForClient': 'param'})
        self.request('All', 'TEST_BLACKLIST', '/validation', doc=False, params={'blacklistParamForAdmin': 'param'})
        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()
        self.request('Client', 'TEST_BLACKLIST', '/validation', doc=False)
        self.request('Client', 'TEST_BLACKLIST', '/validation', doc=False, params={'customParam': 'param'})
        self.request('Client', 'TEST_BLACKLIST', '/validation', doc=False, params={'blacklistParamForAll': 'param'},
                     expected_status=400)
        self.request(
            'Client', 'TEST_BLACKLIST', '/validation', doc=False,
            params={'blacklistParamForClient': 'param'},
            expected_status=400
        )
        self.request('Client', 'TEST_BLACKLIST', '/validation', doc=False, params={
            'blacklistParamForAdmin': 'param'
        })
        # -----------------------------
        # role -> Admin
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()
        self.request('Admin', 'TEST_BLACKLIST', '/validation', doc=False)
        self.request('Admin', 'TEST_BLACKLIST', '/validation', doc=False, params={'customParam': 'param'})
        self.request('Admin', 'TEST_BLACKLIST', '/validation', doc=False, params={'blacklistParamForAll': 'param'},
                     expected_status=400)
        self.request('Admin', 'TEST_BLACKLIST', '/validation', doc=False, params={'blacklistParamForClient': 'param'})
        self.request('Admin', 'TEST_BLACKLIST', '/validation', doc=False, params={'blacklistParamForAdmin': 'param'},
                     expected_status=400)

    def test_validation_exclude(self):
        # Test `exclude`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        result, ___ = self.request(
            'All', 'TEST_EXCLUDE', '/validation', doc=False,
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
            'Client', 'TEST_EXCLUDE', '/validation', doc=False,
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
            'Admin', 'TEST_EXCLUDE', '/validation', doc=False,
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

    def test_validation_filter(self):
        # Test `filter`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        result, ___ = self.request(
            'All', 'TEST_FILTER', '/validation', doc=False,
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
            'Client', 'TEST_FILTER', '/validation', doc=False,
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
            'Admin', 'TEST_FILTER', '/validation', doc=False,
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

    def test_validation_whitelist(self):
        # Test `whitelist`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        result, ___ = self.request('All', 'TEST_WHITELIST', '/validation', doc=False,
                                   params={'whitelistParamForAll': 'param'})
        self.assertIn('whitelistParamForAll', result)
        self.request('All', 'TEST_WHITELIST', '/validation', doc=False)
        self.request(
            'All', 'TEST_WHITELIST', '/validation', doc=False,
            params={
                'whitelistParamForAll': 'param',
                'customParam': 'param'
            },
            expected_status=400
        )
        self.request('All', 'TEST_WHITELIST', '/validation', doc=False, params={'customParam': 'param'},
                     expected_status=400)
        self.request('All', 'TEST_WHITELIST', '/validation', doc=False, params={'whitelistParamForClient': 'param', },
                     expected_status=400)
        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()

        result, ___ = self.request('Client', 'TEST_WHITELIST', '/validation', doc=False,
                                   params={'whitelistParamForAll': 'param'})
        self.assertIn('whitelistParamForAll', result)

        result, ___ = self.request('Client', 'TEST_WHITELIST', '/validation', doc=False,
                                   params={'whitelistParamForClient': 'param'})
        self.assertIn('whitelistParamForClient', result)

        result, ___ = self.request(
            'Client', 'TEST_WHITELIST', '/validation', doc=False,
            params={
                'whitelistParamForAll': 'param',
                'whitelistParamForClient': 'param',
            }
        )
        self.assertIn('whitelistParamForAll', result)
        self.assertIn('whitelistParamForClient', result)

        self.request('Client', 'TEST_WHITELIST', '/validation', doc=False)

        self.request(
            'Client', 'TEST_WHITELIST', '/validation', doc=False,
            params={
                'whitelistParamForAll': 'param',
                'customParam': 'param',
            },
            expected_status=400
        )

        self.request(
            'Client', 'TEST_WHITELIST', '/validation', doc=False,
            params={
                'customParam': 'param',
            },
            expected_status=400
        )

        self.request(
            'Client', 'TEST_WHITELIST', '/validation', doc=False,
            params={
                'whitelistParamForAdmin': 'param',
            },
            expected_status=400
        )

        # -----------------------------
        # role -> Admin
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()

        result, ___ = self.request('Admin', 'TEST_WHITELIST', '/validation', doc=False,
                                   params={'whitelistParamForAll': 'param'})
        self.assertIn('whitelistParamForAll', result)

        result, ___ = self.request('Admin', 'TEST_WHITELIST', '/validation', doc=False,
                                   params={'whitelistParamForAdmin': 'param'})
        self.assertIn('whitelistParamForAdmin', result)

        result, ___ = self.request(
            'Admin', 'TEST_WHITELIST', '/validation', doc=False,
            params={
                'whitelistParamForAll': 'param',
                'whitelistParamForAdmin': 'param',
            }
        )
        self.assertIn('whitelistParamForAll', result)
        self.assertIn('whitelistParamForAdmin', result)

        self.request('Admin', 'TEST_WHITELIST', '/validation', doc=False)

        self.request(
            'Admin', 'TEST_WHITELIST', '/validation', doc=False,
            params={
                'whitelistParamForAll': 'param',
                'customParam': 'param',
            },
            expected_status=400
        )

        self.request('Admin', 'TEST_WHITELIST', '/validation', doc=False, params={
            'customParam': 'param',
        }, expected_status=400)

        self.request(
            'Admin', 'TEST_WHITELIST', '/validation', doc=False,
            params={
                'whitelistParamForAll': 'param',
                'whitelistParamForAdmin': 'param',
                'whitelistParamForClient': 'param',
            },
            expected_status=400
        )

    def test_validation_requires(self):
        # Test `requires`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()

        result, ___ = self.request('All', 'TEST_REQUIRES', '/validation', doc=False,
                                   params={'requiresParamForAll': 'param'})
        self.assertIn('requiresParamForAll', result)

        result, ___ = self.request(
            'All', 'TEST_REQUIRES', '/validation', doc=False,
            params={
                'customParam': 'param',
                'requiresParamForAll': 'param',
            }
        )
        self.assertIn('customParam', result)
        self.assertIn('requiresParamForAll', result)

        self.request('All', 'TEST_REQUIRES', '/validation', doc=False, expected_status=400)

        self.request('All', 'TEST_REQUIRES', '/validation', doc=False, params={'customParam': 'param'},
                     expected_status=400)

        self.request('All', 'TEST_REQUIRES', '/validation', doc=False, params={'requiresParamForClient': 'param'},
                     expected_status=400)

        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()
        result, ___ = self.request(
            'Client', 'TEST_REQUIRES', '/validation', doc=False,
            params={
                'requiresParamForAll': 'param',
                'requiresParamForClient': 'param',
            }
        )
        self.assertIn('requiresParamForAll', result)
        self.assertIn('requiresParamForClient', result)

        result, ___ = self.request(
            'Client', 'TEST_REQUIRES', '/validation', doc=False,
            params={
                'customParam': 'param',
                'requiresParamForAll': 'param',
                'requiresParamForClient': 'param',
            }
        )
        self.assertIn('customParam', result)
        self.assertIn('requiresParamForAll', result)
        self.assertIn('requiresParamForClient', result)

        self.request('Client', 'TEST_REQUIRES', '/validation', doc=False, expected_status=400)

        self.request('Client', 'TEST_REQUIRES', '/validation', doc=False, params={'customParam': 'param'},
                     expected_status=400)

        self.request('Client', 'TEST_REQUIRES', '/validation', doc=False, params={'requiresParamForAll': 'param'},
                     expected_status=400)

        self.request('Client', 'TEST_REQUIRES', '/validation', doc=False, params={
            'requiresParamForClient':
                'param',
        }, expected_status=400)
        # -----------------------------
        # role -> Admin
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()
        result, ___ = self.request('Admin', 'TEST_REQUIRES', '/validation', doc=False, params={
            'requiresParamForAll': 'param',
            'requiresParamForAdmin': 'param',
        })
        self.assertIn('requiresParamForAll', result)
        self.assertIn('requiresParamForAdmin', result)
        result, ___ = self.request(
            'Admin', 'TEST_REQUIRES', '/validation', doc=False,
            params={
                'customParam': 'param',
                'requiresParamForAll': 'param',
                'requiresParamForAdmin': 'param',
            }
        )
        self.assertIn('customParam', result)
        self.assertIn('requiresParamForAll', result)
        self.assertIn('requiresParamForAdmin', result)

        self.request('Admin', 'TEST_REQUIRES', '/validation', doc=False, expected_status=400)

        self.request('Admin', 'TEST_REQUIRES', '/validation', doc=False, params={'customParam': 'param'},
                     expected_status=400)

        self.request(
            'Admin', 'TEST_REQUIRES', '/validation', doc=False,
            params={
                'requiresParamForAll': 'param',
                'requiresParamForClient': 'param',
            },
            expected_status=400
        )

        self.request('Admin', 'TEST_REQUIRES', '/validation', doc=False, params={'requiresParamForAdmin': 'param'},
                     expected_status=400)

    def test_validation_exact(self):
        # Test `exact`
        # role -> All
        self.wsgi_app.jwt_token = DummyIdentity().dump().decode()
        result, ___ = self.request('All', 'TEST_EXACT', '/validation', doc=False, params={'exactParamForAll': 'param'})
        self.request('All', 'TEST_EXACT', '/validation', doc=False, expected_status=400)
        self.request(
            'All', 'TEST_EXACT', '/validation', doc=False,
            params={
                'exactParamForAll': 'param',
                'exactParamForCustom': 'param',
            },
            expected_status=400
        )
        self.request('All', 'TEST_EXACT', '/validation', doc=False, params={'exactParamForCustom': 'param'},
                     expected_status=400)
        self.assertIn('exactParamForAll', result)
        self.request(
            'All', 'TEST_EXACT', '/validation', doc=False,
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
            'Client', 'TEST_EXACT', '/validation', doc=False,
            params={
                'exactParamForAll': 'param',
                'exactParamForClient': 'param',
            }
        )
        self.assertIn('exactParamForClient', result)
        self.assertIn('exactParamForAll', result)

        self.request(
            'Client', 'TEST_EXACT', '/validation', doc=False,
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

        result, ___ = self.request('Admin', 'TEST_EXACT', '/validation', doc=False, params={
            'exactParamForAll': 'param',
            'exactParamForAdmin': 'param',
        })
        self.assertIn('exactParamForAdmin', result)
        self.assertIn('exactParamForAll', result)

        self.request('Admin', 'TEST_EXACT', '/validation', doc=False, params={
            'exactParamForAll': 'param',
            'exactParamForClient': 'param',
            'exactParamForAdmin': 'param',
        }, expected_status=400)

        # ------------------------------------------------------------

        # Test query string
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()
        result, ___ = self.request(
            'Admin', 'TEST_EXACT', '/validation', doc=False,
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
            'Admin', 'TEST_EXACT', '/validation', doc=False,
            query_string={
                'exactParamForAll': 'param',
                'exactParamForClient': 'param',
            },
            params={'exactParamForAdmin': 'param'}, expected_status=400
        )


if __name__ == '__main__':
    unittest.main()
