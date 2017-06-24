import copy
import unittest

from nanohttp import context, json, settings

from restfulpy.principal import DummyIdentity
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.validation import validate_form
from restfulpy.controllers import RestController, RootController


class ValidationBlackListController(RestController):
    @json
    @validate_form(blacklist=['blacklistParamForAll'],
                   client={'blacklist': ['blacklistParamForClient']},
                   admin={'blacklist': ['blacklistParamForAdmin']})
    def post(self):
        result = copy.deepcopy(context.form)
        result.update(context.query_string)
        return result


class Root(RootController):
    validation = ValidationBlackListController()


class ValidationBlackListTestCase(WebAppTestCase):
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
        self.request('All', 'POST', '/validation', doc=False)
        self.request('All', 'POST', '/validation', doc=False, params={'customParam': 'param'})
        self.request('All', 'POST', '/validation', doc=False, params={'blacklistParamForAll': 'param'},
                     expected_status=400)
        self.request('All', 'POST', '/validation', doc=False, params={'blacklistParamForClient': 'param'})
        self.request('All', 'POST', '/validation', doc=False, params={'blacklistParamForAdmin': 'param'})
        # -----------------------------
        # role -> Client
        self.wsgi_app.jwt_token = DummyIdentity('client').dump().decode()
        self.request('Client', 'POST', '/validation', doc=False)
        self.request('Client', 'POST', '/validation', doc=False, params={'customParam': 'param'})
        self.request('Client', 'POST', '/validation', doc=False, params={'blacklistParamForAll': 'param'},
                     expected_status=400)
        self.request(
            'Client', 'POST', '/validation', doc=False,
            params={'blacklistParamForClient': 'param'},
            expected_status=400
        )
        self.request('Client', 'POST', '/validation', doc=False, params={
            'blacklistParamForAdmin': 'param'
        })
        # -----------------------------
        # role -> Admin
        self.wsgi_app.jwt_token = DummyIdentity('admin').dump().decode()
        self.request('Admin', 'POST', '/validation', doc=False)
        self.request('Admin', 'POST', '/validation', doc=False, params={'customParam': 'param'})
        self.request('Admin', 'POST', '/validation', doc=False, params={'blacklistParamForAll': 'param'},
                     expected_status=400)
        self.request('Admin', 'POST', '/validation', doc=False, params={'blacklistParamForClient': 'param'})
        self.request('Admin', 'POST', '/validation', doc=False, params={'blacklistParamForAdmin': 'param'},
                     expected_status=400)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
