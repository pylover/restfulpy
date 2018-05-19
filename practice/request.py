from nanohttp import json, Controller, context, settings
from restfulpy.authentication import StatefulAuthenticator
from restfulpy.authorization import authorize
from restfulpy.principal import JwtPrincipal, JwtRefreshToken
from restfulpy.testing import WebAppTestCase, As
from restfulpy.tests.helpers import MockupApplication


class MockupMember:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


roles = ['admin', 'test']


class MockupAuthenticator(StatefulAuthenticator):
    def validate_credentials(self, credentials):
        email, password = credentials
        if password == 'test':
            return MockupMember(id=1, email=email, roles=['admin', 'test'])

    def create_refresh_principal(self, member_id=None):
        return JwtRefreshToken(dict(
            id=member_id
        ))

    def create_principal(self, member_id=None, session_id=None):
        return JwtPrincipal(dict(id=1, email='test@example.com', roles=roles, sessionId='1'))


class Root(Controller):
    @json
    def login(self):
        principal = context.application.__authenticator__.login((context.form['email'], context.form['password']))
        return dict(token=principal.dump())

    @json
    @authorize
    def invalidate_token(self):
        context.application.__authenticator__.invalidate_member(1)
        return context.identity.payload


class StatefulAuthenticatorTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', Root(), authenticator=MockupAuthenticator())

    @classmethod
    def configure_app(cls):
        cls.application.configure(force=True)
        settings.merge("""
            jwt:
              max_age: .3
              refresh_token:
                max_age: 3                
        """)

    def test_invalidate_token(self):
        principal = JwtPrincipal(dict(
            email='test@example.com',
            id=1,
            sessionId=1,
            roles=roles
        ))

        response, headers = self.request('ALL', 'GET', '/login', json=dict(email='test@example.com', password='test'))
        print('\n' , principal.dump())

        print('Print refresh token')

        print('refresh-token=' + JwtRefreshToken(dict(id = 1)).dump().decode("utf-8"))
        print(headers['Set-Cookie'].split('; ')[0])

