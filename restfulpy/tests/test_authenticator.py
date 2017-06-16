

import unittest

from nanohttp import json, Controller, context

from restfulpy.authentication import Authenticator
from restfulpy.principal import JwtPrincipal, JwtRefreshToken
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication


class MockupMember:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class MockupStatelessAuthenticator(Authenticator):
    def validate_credentials(self, credentials):
        email, password = credentials
        if password == 'test':
            return MockupMember(id=1, email=email, roles=['admin', 'test'])
        return None

    def create_refresh_principal(self, member_id=None):
        return JwtRefreshToken(dict(
            id=member_id
        ))

    def create_principal(self, member_id=None, session_id=None):
        return JwtPrincipal(dict(id=1, email='test@example.com', roles=['admin', 'test']))


class Root(Controller):

    @json
    def index(self):
        return context.form

    @json
    def login(self):
        principal = context.application.__authenticator__.login((context.form['email'], context.form['password']))
        return dict(token=principal.dump())


class AuthenticatorTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', Root(), authenticator=MockupStatelessAuthenticator())

    def test_login(self):
        response, headers = self.request('ALL', 'GET', '/login', json=dict(email='test@example.com', password='test'))
        self.assertIn('token', response)
        self.assertEqual(headers['X-Identity'], '1')

        self.wsgi_app.jwt_token = response['token']
        response, headers = self.request('ALL', 'GET', '/', json=dict(a='a', b='b'))
        self.assertEqual(headers['X-Identity'], '1')


if __name__ == '__main__':
    unittest.main()