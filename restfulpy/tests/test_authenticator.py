import itsdangerous
from bddrest.authoring import response, when
from nanohttp import json, Controller, context, HTTPBadRequest, settings

from restfulpy.mockup import MockupApplication
from restfulpy.authentication import Authenticator
from restfulpy.authorization import authorize
from restfulpy.principal import JwtPrincipal, JwtRefreshToken
from restfulpy.testing import ApplicableTestCase


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
        return JwtPrincipal(dict(
            id=1,
            email='test@example.com',
            roles=['admin', 'test'],
            sessionId='1')
        )

    def verify_token(self, encoded_token):
        principal = super().verify_token(encoded_token)
        if token_expired:
            raise itsdangerous.SignatureExpired(
                'Simulating',
                payload=principal.payload
            )
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
        principal = context.application.__authenticator__.login(
            (context.form['email'], context.form['password'])
        )
        if principal:
            return dict(token=principal.dump())
        raise HTTPBadRequest()

    @json
    @authorize
    def me(self):
        return context.identity.payload

    @json()
    @authorize
    def logout(self):
        context.application.__authenticator__.logout()
        return {}

    @json
    @authorize('god')
    def kill(self):  # pragma: no cover
        context.application.__authenticator__.logout()
        return {}


class TestAuthenticator(ApplicableTestCase):
    __application__ = MockupApplication(
        'Authenticator Application',
        Root(),
        authenticator=MockupStatelessAuthenticator()
    )

    __configuration__ = ('''
        jwt:
          max_age: .3
          refresh_token:
            max_age: 3
            secure: true
    ''')

    def test_login(self):
        with self.given(
                'Loggin in to get a token',
                '/login',
                'POST',
                form=dict(email='test@example.com', password='test')
            ):
            assert response.status == '200 OK'
            assert response.headers['X-Identity'] == '1'
            assert 'token' in response.json
            token = response.json['token']

            when(
                'Password is incorrect',
                form=dict(email='test@example.com', password='invalid')
            )
            assert response.status == '400 Bad Request'

        with self.given(
                'Trying to access a protected resource with the token',
                '/',
                'GET',
                form=dict(a='a', b='b'),
                authorization=token
            ):
            assert response.headers['X-Identity'] == '1'

            when('Token is broken', authorization='bad')
            assert response.status == 400

            when('Token is empty', url='/me', authorization='')
            assert response.status == 401

    def test_logout(self):
        self.login(
            dict(
                email='test@example.com',
                password='test'
            ),
            url='/login',
            verb='POST'
        )

        with self.given(
                'Logging out',
                '/logout',
            ):
            assert response.status == '200 OK'
            assert 'X-Identity' not in response.headers

    def test_refresh_token(self):
        global token_expired, refresh_token_expired
        self.logout()
        with self.given(
                'Loggin in to get a token',
                '/login',
                'POST',
                form=dict(email='test@example.com', password='test')
            ):
            refresh_token = response.headers['Set-Cookie'].split('; ')[0]
            assert 'token' in response.json
            assert refresh_token.startswith('refresh-token=')
            token = response.json['token']

            # Login on client
            token_expired = True
            settings.jwt.refresh_token.secure = False


        # Request a protected resource after the token has been expired,
        # with broken cookies
        with self.given(
                    'Refresh token is broken',
                    url='/me',
                    verb='GET',
                    authorization=token,
                    headers={
                        'Cookie': 'refresh-token=broken-data'
                    }
            ):
            assert response.status == 400

            # Request a protected resource after the token has been expired,
            # with empty cookies
            when(
                'Refresh token is empty',
                headers={
                    'Cookie': 'refresh-token'
                }
            )
            assert response.status == 401

            # Request a protected resource after the token has been expired,
            # without the cookies
            when(
                'Without the cookies',
                headers=None
            )
            assert response.status == 401

            # Request a protected resource after the token has been expired,
            # with appropriate cookies.
            when(
                'With appropriate cookies',
                headers={
                    'Cookie': refresh_token
                }
            )
            assert 'X-New-JWT-Token' in response.headers
            assert response.headers['X-New-JWT-Token'] is not None

            # Test with invalid refresh token
            when(
                'With invalid refresh token',
                headers={
                    'Cookie': 'refresh-token=InvalidToken'
                }
            )
            assert response.status == 400

            # Waiting until expire refresh token
            refresh_token_expired = True

            # Request a protected resource after
            # the refresh-token has been expired.
            when(
                'The refresh token has been expired.',
                 headers={
                    'Cookie': 'refresh-token'
                 }
            )
            assert response.status == 401

    def test_authorization(self):
        global token_expired
        self.login(
            dict(
                email='test@example.com',
                password='test'
            ),
            url='/login'
        )
        token_expired = False

        with self.given(
            'Access forbidden',
            url='/kill',
            verb='GET'
        ):
            assert response.status == 403

