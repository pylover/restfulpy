import time
import unittest

from nanohttp import settings
from restfulpy.authentication import StatefulAuthenticator
from restfulpy.principal import JwtPrincipal, JwtRefreshToken
from restfulpy.tests.helpers import WebAppTestCase
from restfulpy.testing import MockupApplication


roles = ['admin', 'test']


class MockupAuthenticator(StatefulAuthenticator):
    def validate_credentials(self, credentials):
        raise NotImplementedError()

    def create_refresh_principal(self, member_id=None):
        return JwtRefreshToken(dict(
            id=member_id
        ))

    def create_principal(self, member_id=None, session_id=None, **kwargs):
        return JwtPrincipal(dict(id=1, email='test@example.com', roles=roles, sessionId='1'))


class StatefulAuthenticatorTestCase(WebAppTestCase):
    application = MockupApplication(
        'MockupApplication', None, authenticator=MockupAuthenticator())

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
        principal = self.application.__authenticator__.create_principal()

        token = principal.dump().decode("utf-8")
        refresh_principal = self.application.__authenticator__.\
            create_refresh_principal()
        refresh_token = 'refresh-token=' + refresh_principal.dump().\
            decode("utf-8")
        self.assertTrue(refresh_token.startswith('refresh-token='))
        self.wsgi_application.jwt_token = token

        time.sleep(1)

        self.request(
            'member',
            'GET',
            '/',
            headers={'Cookie': refresh_token},
            expected_status='400 not allowed'
        )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
