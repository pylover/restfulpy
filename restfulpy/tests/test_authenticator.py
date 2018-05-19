import unittest

import itsdangerous
from nanohttp import json, Controller, context, HttpBadRequest, settings

from restfulpy.authentication import Authenticator
from restfulpy.authorization import authorize
from restfulpy.principal import JwtPrincipal, JwtRefreshToken
from restfulpy.testing import WebAppTestCase, As
from restfulpy.tests.helpers import MockupApplication


token_expired = False
refresh_token_expired = False


class MockupMember:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class MockupStatelessAuthenticator(Authenticator):
    def validate_credentials(self, credentials):
        email, password = credentials
        if password == 'test':
            return MockupMember(id=1, email=email, roles=['admin', 'test'])

    def create_refresh_principal(self, member_id=None):
        return JwtRefreshToken(dict(
            id=member_id
        ))

    def create_principal(self, member_id=None, session_id=None):
        return JwtPrincipal(dict(id=1, email='test@example.com', roles=['admin', 'test'], sessionId='1'))

    def verify_token(self, encoded_token):
        principal = super().verify_token(encoded_token)
        if token_expired:
            raise itsdangerous.SignatureExpired('Simulating', payload=principal.payload)
        return principal

    def try_refresh_token(self, session_id):
        if refresh_token_expired:
            self.bad()
        return super().try_refresh_token(session_id)


class Root(Controller):
    @json
    def index(self):
        return context.form

    @json(verbs='post')
    def login(self):
        principal = context.application.__authenticator__.login((context.form['email'], context.form['password']))
        if principal:
            return dict(token=principal.dump())
        raise HttpBadRequest()

    @json
    @authorize
    def me(self):
        return context.identity.payload

    @json(verbs='delete')
    @authorize
    def logout(self):
        context.application.__authenticator__.logout()
        return {}

    @json
    @authorize('god')
    def kill(self):  # pragma: no cover
        context.application.__authenticator__.logout()
        return {}


class AuthenticatorTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', Root(), authenticator=MockupStatelessAuthenticator())

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

    def test_login(self):
        response, headers = self.request('ALL', 'POST', '/login', json=dict(email='test@example.com', password='test'))
        self.assertIn('token', response)
        self.assertEqual(headers['X-Identity'], '1')

        self.wsgi_app.jwt_token = response['token']
        response, headers = self.request('ALL', 'GET', '/', json=dict(a='a', b='b'))
        self.assertEqual(headers['X-Identity'], '1')

        # Broken token
        self.wsgi_app.jwt_token = self.wsgi_app.jwt_token[:-10]
        self.request('ALL', 'GET', '/', expected_status=400)

        # Empty
        self.wsgi_app.jwt_token = ' '
        self.request('ALL', 'GET', '/me', expected_status=401)

        # Bad Password
        self.wsgi_app.jwt_token = None
        self.request(
            'ALL', 'POST', '/login',
            json=dict(email='test@example.com', password='bad'),
            expected_status=400
        )

    def test_logout(self):
        response, headers = self.request('ALL', 'POST', '/login', json=dict(email='test@example.com', password='test'))
        self.assertIn('token', response)
        self.assertEqual(headers['X-Identity'], '1')
        self.wsgi_app.jwt_token = response['token']
        response, headers = self.request('ALL', 'DELETE', '/logout')
        self.assertNotIn('X-Identity', headers)

    def test_refresh_token(self):
        global token_expired, refresh_token_expired
        self.wsgi_app.jwt_token = None
        response, headers = self.request('ALL', 'POST', '/login', json=dict(email='test@example.com', password='test'))
        refresh_token = headers['Set-Cookie'].split('; ')[0]
        self.assertIn('token', response)
        self.assertTrue(refresh_token.startswith('refresh-token='))

        # Login on client
        token = response['token']
        self.wsgi_app.jwt_token = token
        token_expired = True
        settings.jwt.refresh_token.secure = False
        # Request a protected resource after the token has been expired, with broken cookies
        self.request(
            As.member, 'GET', '/me',
            headers={
                'Cookie': 'refresh-token=broken-data'
            },
            expected_status=400
        )

        # Request a protected resource after the token has been expired, with empty cookies
        self.request(
            As.member, 'GET', '/me',
            headers={
                'Cookie': 'refresh-token='
            },
            expected_status=401
        )

        # Request a protected resource after the token has been expired, without the cookies
        self.request(As.member, 'GET', '/me', expected_status=401)

        # Request a protected resource after the token has been expired, with appropriate cookies.
        response, response_headers = self.request(
            As.member, 'GET', '/me',
            headers={
                'Cookie': refresh_token
            }
        )
        self.assertIn('X-New-JWT-Token', response_headers)
        self.assertIsNotNone(response_headers['X-New-JWT-Token'])

        # Test with invalid Refresh Token
        self.request(
            As.member, 'GET', '/me',
            headers={
                'Cookie': 'refresh-token=InvalidToken'
            },
            expected_status=400
        )

        # Waiting until expire refresh token
        refresh_token_expired = True
        # Request a protected resource after the refresh-token has been expired.
        self.request(
            As.member, 'GET', '/me',
            headers={
                'Cookie': refresh_token
            },
            expected_status=401
        )

    def test_authorization(self):
        response, headers = self.request('ALL', 'POST', '/login', json=dict(email='test@example.com', password='test'))
        self.assertIn('token', response)
        self.assertEqual(headers['X-Identity'], '1')
        self.wsgi_app.jwt_token = response['token']
        response, headers = self.request('ALL', 'GET', '/kill', expected_status=403)
        self.assertEqual(headers['X-Identity'], '1')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
