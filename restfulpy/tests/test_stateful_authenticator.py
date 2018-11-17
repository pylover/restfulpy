import time

from bddrest import status, response, when
from freezegun import freeze_time
from nanohttp import json, Controller, context
from nanohttp.contexts import Context

from restfulpy.mockup import MockupApplication
from restfulpy.authentication import StatefulAuthenticator
from restfulpy.authorization import authorize
from restfulpy.principal import JwtPrincipal, JwtRefreshToken
from restfulpy.testing import ApplicableTestCase


class MockupMember:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


roles = ['admin', 'test']


class MockupStatefulAuthenticator(StatefulAuthenticator):
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
            roles=roles,
            sessionId='1'
        ))


class Root(Controller):
    @json
    def login(self):
        principal = context.application.__authenticator__.login(
            (context.form['email'], context.form['password'])
        )
        return dict(token=principal.dump())

    @json
    @authorize
    def me(self):
        return context.identity.payload

    @json
    @authorize
    def invalidate_token(self):
        context.application.__authenticator__.invalidate_member(1)
        return context.identity.payload

    @json(verbs='delete')
    @authorize
    def logout(self):
        context.application.__authenticator__.logout()
        return {}


class TestStatefulAuthenticator(ApplicableTestCase):
    __application__ = MockupApplication(
        'Stateful Authenticator Application',
        Root(),
        authenticator=MockupStatefulAuthenticator()
    )

    __configuration__ = '''
        jwt:
          max_age: .3
          refresh_token:
            max_age: 3
            secure: false
    '''

    def test_invalidate_token(self):
        with self.given(
                'Log in to get a token and refresh token cookie',
                '/login',
                'POST',
                form=dict(email='test@example.com', password='test')
            ):
            assert status == 200
            assert 'token' in response.json
            refresh_token = response.headers['Set-Cookie'].split('; ')[0]
            assert refresh_token.startswith('refresh-token=')

            # Store token to use it for future requests
            token = response.json['token']
            self._authentication_token = token

        with self.given(
                'Request a protected resource to ensure authenticator is '
                'working well',
                '/me',
                headers={'Cookie': refresh_token}
            ):
            assert status == 200
            assert response.json['roles'] == roles

            roles.append('god')
            when(
                'Invalidating the token by server',
                '/invalidate_token'
            )
            assert response.json['roles'] == roles
            assert 'X-New-JWT-Token' in response.headers

            when(
                'Invalidating the token by server after the token has '
                'been expired, with appropriate cookies.',
                '/invalidate_token',
            )
            time.sleep(1)
            assert 'X-New-JWT-Token' in response.headers
            assert response.headers['X-New-JWT-Token'] is not None
            self._authentication_token = response.headers['X-New-JWT-Token']

            when(
                'Requesting a resource with new token',
                '/me',
            )
            assert status == 200

    def test_logout(self):
        with self.given(
                'Log in to get a token and refresh token cookie',
                '/login',
                'POST',
                form=dict(email='test@example.com', password='test')
            ):
            assert status == 200
            assert 'token' in response.json
            assert response.headers['X-Identity'] == '1'
            self._authentication_token = response.json['token']

            when(
                'Logging out',
                '/logout',
                'DELETE'
            )
            assert 'X-Identity' not in response.headers

    def test_session_member(self):
        with Context(environ={}, application=self.__application__):
            authenticator = self.__application__.__authenticator__
            principal = authenticator.login(
                ('test@example.com', 'test')
            )
            assert authenticator.get_member_id_by_session(
                principal.session_id
            ) == 1

    @freeze_time("2017-07-13T13:11:44", tz_offset=-4)
    def test_session_info(self):
        with self.given(
                'Log in to get a token and refresh token cookie',
                '/login',
                'POST',
                form=dict(email='test@example.com', password='test')
            ):
            assert status == 200
            assert 'token' in response.json
            assert response.headers['X-Identity'] == '1'
            self._authentication_token = response.json['token']

            # Testing test cases
            for test_case in session_info_test_cases:
                # Our new session info should be updated
                self.when(
                    'Getting session info',
                    '/me',
                    extra_environ=test_case['environment']
                )
                assert status == 200
                assert 'sessionId' in response.json

                info = self.__application__.__authenticator__\
                    .get_session_info(response.json['sessionId'])

                assert info.items() == {
                    'remoteAddress': test_case['expected_remote_address'],
                    'machine': test_case['expected_machine'],
                    'os': test_case['expected_os'],
                    'agent': test_case['expected_agent'],
                    'lastActivity': test_case['expected_last_activity'],
                }.items()


session_info_test_cases = [
    {
        'environment': {
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_USER_AGENT': \
                'Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) '
                'AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 '
                'Mobile/9B179 Safari/7534.48.3 RestfulpyClient-js/1.2.3 (My '
                'App; test-name; 1.4.5-beta78; fa-IR; some; extra; info)'
        },
        'expected_remote_address': '127.0.0.1',
        'expected_machine': 'iPhone',
        'expected_os': 'iOS 5.1',
        'expected_agent': 'Mobile Safari 5.1',
        'expected_last_activity': '2017-07-13T13:11:44',
    },
    {
        'environment': {
            'REMOTE_ADDR': '185.87.34.23',
            'HTTP_USER_AGENT': \
                'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; '
                'Trident/5.0) RestfulpyClient-custom/4.5.6 (A; B; C)'
        },
        'expected_remote_address': '185.87.34.23',
        'expected_machine': 'PC',
        'expected_os': 'Windows 7',
        'expected_agent': 'IE 9.0',
        'expected_last_activity': '2017-07-13T13:11:44',
    },
    {
        'environment': {
            'REMOTE_ADDR': '172.16.0.111',
            'HTTP_USER_AGENT': ''
        },
        'expected_remote_address': '172.16.0.111',
        'expected_machine': 'Other',
        'expected_os': 'Other',
        'expected_agent': 'Other',
        'expected_last_activity': '2017-07-13T13:11:44',
    },
    {
        'environment': {},
        'expected_remote_address': '127.0.0.1',
        'expected_machine': 'Other',
        'expected_os': 'Other',
        'expected_agent': 'Other',
        'expected_last_activity': '2017-07-13T13:11:44',
    }
]
