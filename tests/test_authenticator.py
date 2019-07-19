import itsdangerous
from freezegun import freeze_time
from bddrest.authoring import response, when, status
from nanohttp import json, Controller, context, HTTPBadRequest, settings

from restfulpy.mockup import MockupApplication
from restfulpy.authentication import Authenticator
from restfulpy.authorization import authorize
from restfulpy.principal import JWTPrincipal, JWTRefreshToken
from restfulpy.testing import ApplicableTestCase


token_expired = False


class MockupMember:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class MockupStatelessAuthenticator(Authenticator):
    def validate_credentials(self, credentials):
        email, password = credentials
        if password == 'test':
            return MockupMember(id=1, email=email, roles=['admin', 'test'])

    def create_refresh_principal(self, member_id=None):
        return JWTRefreshToken(dict(
            id=member_id
        ))

    def create_principal(self, member_id=None, session_id=None):
        return JWTPrincipal(dict(
            id=1,
            email='test@example.com',
            roles=['admin', 'test'],
            sessionId='1')
        )


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
          max_age: 10
          refresh_token:
            max_age: 20
            secure: false
            path: /
    ''')

    def test_login(self):
        logintime = freeze_time("2000-01-01T01:01:00")
        latetime = freeze_time("2000-01-01T01:01:12")
        with logintime, self.given(
                'Loggin in to get a token',
                '/login',
                'POST',
                form=dict(email='test@example.com', password='test')
            ):
            assert status == '200 OK'
            assert response.headers['X-Identity'] == '1'
            assert 'token' in response.json
            token = response.json['token']

            when(
                'Password is incorrect',
                form=dict(email='test@example.com', password='invalid')
            )
            assert status == '400 Bad Request'

        with logintime, self.given(
                'Trying to access a protected resource with the token',
                '/me',
                authorization=token
            ):
            assert response.headers['X-Identity'] == '1'

            when('Token is broken', authorization='bad')
            assert status == 400

            when('Token is empty', url='/me', authorization='')
            assert status == 401

            when('Token is blank', url='/me', authorization='  ')
            assert status == 401

        with latetime, self.given(
                'Try to access a protected resource when session is expired',
                '/me',
                form=dict(a='a', b='b'),
                authorization=token
        ):
            assert status == 401


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
            assert status == '200 OK'
            assert 'X-Identity' not in response.headers

    def test_refresh_token(self):
        logintime = freeze_time("2000-01-01T01:01:00")
        latetime = freeze_time("2000-01-01T01:01:12")
        verylatetime = freeze_time("2000-01-01T01:02:00")
        self.logout()
        with logintime, self.given(
                'Loggin in to get a token',
                '/login',
                'POST',
                form=dict(email='test@example.com', password='test')
            ):
            refresh_token = response.headers['Set-Cookie'].split('; ')[0]
            assert 'token' in response.json
            assert refresh_token.startswith('refresh-token=')
            token = response.json['token']


        # Request a protected resource after the token has been expired,
        # with broken cookies
        with latetime, self.given(
                'Refresh token is broken',
                '/me',
                authorization=token,
                headers={
                    'Cookie': 'refresh-token=broken-data'
                }
        ):
            assert status == 400

            # Request a protected resource after the token has been expired,
            # with empty cookies
            when(
                'Refresh token is empty',
                headers={
                    'Cookie': 'refresh-token'
                }
            )
            assert status == 401

            # Request a protected resource after the token has been expired,
            # without the cookies
            when(
                'Without the cookies',
                headers=None
            )
            assert status == 401

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

            when(
                'With invalid refresh token',
                headers={
                    'Cookie': 'refresh-token=InvalidToken'
                }
            )
            assert status == 400

            when(
                'With empty refresh token',
                headers={
                    'Cookie': 'refresh-token='
                }
            )
            assert status == 401

        with verylatetime, self.given(
            'When refresh token is expired',
            '/me',
            authorization=token,
            headers={
                'Cookie': refresh_token
            }
        ):

            assert status == 401

    def test_authorization(self):
        self.login(
            dict(
                email='test@example.com',
                password='test'
            ),
            url='/login'
        )

        with self.given(
            'Access forbidden',
            url='/kill',
            verb='GET'
        ):
            assert status == 403

