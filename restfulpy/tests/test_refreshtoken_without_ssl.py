import time
import unittest
from nanohttp import Controller, settings
from restfulpy.authentication import StatefulAuthenticator
from restfulpy.principal import JwtPrincipal, JwtRefreshToken
from restfulpy.tests.helpers import WebAppTestCase
from restfulpy.testing import MockupApplication


roles = ['admin', 'test']


class MockupAuthenticator(StatefulAuthenticator):
    pass


class Root(Controller):
    pass


class StatefulAuthenticatorTestCase(WebAppTestCase):
    application = MockupApplication(
        'MockupApplication', Root(), authenticator=MockupAuthenticator())

    @classmethod
    def configure_app(cls):
        cls.application.configure(force=True)
        settings.merge("""
            jwt:
              max_age: .3
              refresh_token:
                max_age: 3
                secure: true
        """)

    def test_invalidate_token(self):
        principal = JwtPrincipal(dict(
            email='test@example.com',
            id=1,
            sessionId=1,
            roles=roles
        ))

        token = principal.dump().decode("utf-8")
        refresh_token = 'refresh-token=' + JwtRefreshToken(dict(id=1)).dump().decode("utf-8")
        self.assertTrue(refresh_token.startswith('refresh-token='))
        self.wsgi_application.jwt_token = token

        time.sleep(1)
        self.request('member', 'GET', '/me', headers={'Cookie': refresh_token}, expected_status=400)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
