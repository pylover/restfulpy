import time

from bddrest.authoring import response

from restfulpy.mockup import MockupApplication
from restfulpy.authentication import StatefulAuthenticator
from restfulpy.principal import JwtPrincipal, JwtRefreshToken
from restfulpy.testing import ApplicableTestCase


roles = ['admin', 'test']


class MockupAuthenticator(StatefulAuthenticator):
    def validate_credentials(self, credentials):
        raise NotImplementedError()

    def create_refresh_principal(self, member_id=None):
        return JwtRefreshToken(dict(
            id=member_id
        ))

    def create_principal(self, member_id=None, session_id=None, **kwargs):
        return JwtPrincipal(
            dict(id=1, email='test@example.com', roles=roles, sessionId='1')
        )


class TestRefreshTokenWithoutSSl(ApplicableTestCase):
    __application__ = MockupApplication(
        'MockupApplication',
        None,
        authenticator=MockupAuthenticator()
    )

    __configuration__ = ('''
        jwt:
          max_age: .3
          refresh_token:
            max_age: 3
            secure: true
    ''')

    def test_refresh_token_security(self):
        principal = self.__application__.__authenticator__.create_principal()

        token = principal.dump().decode("utf-8")
        refresh_principal = self.__application__.__authenticator__.\
            create_refresh_principal()
        refresh_token = 'refresh-token=' + refresh_principal.dump().\
            decode("utf-8")
        assert refresh_token.startswith('refresh-token=') is True
        self._authentication_token = token

        time.sleep(1)

        with self.given(
            'Refresh tokn can not be set in not secure connections',
            headers={'Cookie': refresh_token},
        ):
            assert response.status == 400

