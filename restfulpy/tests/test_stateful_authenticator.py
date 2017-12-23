import unittest
import time

from freezegun import freeze_time
from nanohttp import json, Controller, context, settings
from nanohttp.contexts import Context

from restfulpy.authentication import StatefulAuthenticator
from restfulpy.authorization import authorize
from restfulpy.principal import JwtPrincipal, JwtRefreshToken
from restfulpy.testing import WebAppTestCase, As
from restfulpy.tests.helpers import MockupApplication

session_info_test_cases = [
    {
        'environment': {
            'REMOTE_ADDR': '',
            'HTTP_USER_AGENT': 'Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) AppleWebKit/534.46 (KHTML, '
                               'like Gecko) Version/5.1 Mobile/9B179 Safari/7534.48.3 RestfulpyClient-js/1.2.3 (My '
                               'App; test-name; 1.4.5-beta78; fa-IR; some; extra; info)'
        },
        'expected_remote_address': 'NA',
        'expected_machine': 'iPhone',
        'expected_os': 'iOS 5.1',
        'expected_agent': 'Mobile Safari 5.1',
        'expected_client': 'RestfulpyClient-js 1.2.3',
        'expected_app': 'My App (test-name) 1.4.5-beta78',
        'expected_last_activity': '2017-07-13T13:11:44',
    },
    {
        'environment': {
            'REMOTE_ADDR': '185.87.34.23',
            'HTTP_USER_AGENT': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0) '
                               'RestfulpyClient-custom/4.5.6 (A; B; C)'
        },
        'expected_remote_address': '185.87.34.23',
        'expected_machine': 'PC',
        'expected_os': 'Windows 7',
        'expected_agent': 'IE 9.0',
        'expected_client': 'RestfulpyClient-custom 4.5.6',
        'expected_app': 'A (B) C',
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
        'expected_client': 'Unknown',
        'expected_app': 'Unknown',
        'expected_last_activity': '2017-07-13T13:11:44',
    },
    {
        'environment': {},
        'expected_remote_address': 'NA',
        'expected_machine': 'Other',
        'expected_os': 'Other',
        'expected_agent': 'Other',
        'expected_client': 'Unknown',
        'expected_app': 'Unknown',
        'expected_last_activity': '2017-07-13T13:11:44',
    }
]


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
        return JwtPrincipal(dict(id=1, email='test@example.com', roles=roles, sessionId='1'))


class Root(Controller):
    @json
    def login(self):
        principal = context.application.__authenticator__.login((context.form['email'], context.form['password']))
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


class StatefulAuthenticatorTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', Root(), authenticator=MockupStatefulAuthenticator())

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
        response, headers = self.request('ALL', 'GET', '/login', json=dict(email='test@example.com', password='test'))
        refresh_token = headers['Set-Cookie'].split('; ')[0]
        self.assertIn('token', response)
        self.assertTrue(refresh_token.startswith('refresh-token='))

        # Login on client
        token = response['token']
        self.wsgi_app.jwt_token = token

        # Request a protected resource to ensure authenticator is working well
        response, ___ = self.request(As.member, 'GET', '/me', headers={'Cookie': refresh_token})
        self.assertListEqual(response['roles'], roles)

        # Invalidating the token by server
        roles.append('god')
        response, headers = self.request(As.member, 'GET', '/invalidate_token', headers={'Cookie': refresh_token})
        self.assertListEqual(response['roles'], roles)
        self.assertIn('X-New-JWT-Token', headers)

        # Invalidating the token by server after the token has been expired expired, with appropriate cookies.
        time.sleep(1)
        response, headers = self.request(
            As.member, 'GET', '/invalidate_token',
            headers={
                'Cookie': refresh_token
            }
        )
        self.assertIn('X-New-JWT-Token', headers)
        self.assertIsNotNone(headers['X-New-JWT-Token'])
        self.wsgi_app.jwt_token = headers['X-New-JWT-Token']
        self.request(As.member, 'GET', '/me', headers={'Cookie': refresh_token})

    def test_logout(self):
        response, headers = self.request('ALL', 'POST', '/login', json=dict(email='test@example.com', password='test'))
        self.assertIn('token', response)
        self.assertEqual(headers['X-Identity'], '1')
        self.wsgi_app.jwt_token = response['token']
        response, headers = self.request('ALL', 'DELETE', '/logout')
        self.assertNotIn('X-Identity', headers)

    def test_session_member(self):
        with Context(environ={}, application=self.application):
            principal = self.application.__authenticator__.login(('test@example.com', 'test'))
            self.assertEqual(self.application.__authenticator__.get_session_member(principal.session_id), 1)

    @freeze_time("2017-07-13T13:11:44", tz_offset=-4)
    def test_session_info(self):
        # Login
        response, headers = self.request('ALL', 'GET', '/login', json=dict(email='test@example.com', password='test'))
        self.wsgi_app.jwt_token = response['token']

        # Testing test cases
        for test_case in session_info_test_cases:
            # Our new session info should be updated
            payload, ___ = self.request(As.member, 'GET', '/me', extra_environ=test_case['environment'])

            info = self.application.__authenticator__.get_session_info(payload['sessionId'])
            self.assertDictEqual(info, {
                'remoteAddress': test_case['expected_remote_address'],
                'machine': test_case['expected_machine'],
                'os': test_case['expected_os'],
                'agent': test_case['expected_agent'],
                'client': test_case['expected_client'],
                'app': test_case['expected_app'],
                'lastActivity': test_case['expected_last_activity'],
            })


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
