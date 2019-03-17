import json

import pytest
from bddcli import Given, given, when, stdout, stderr, Application
from itsdangerous import TimedJSONWebSignatureSerializer
from itsdangerous.exc import SignatureExpired
from nanohttp import settings

from restfulpy import Application as RestfulpyApplication


foo = RestfulpyApplication(name='jwt')
foo.__configuration__ = ''


def foo_main():
    return foo.cli_main()


app = Application('foo', 'restfulpy.tests.test_jwt_cli:foo_main')


def test_jwt():
    foo.configure(force=True)
    pirincipal = TimedJSONWebSignatureSerializer(
        settings.jwt.secret,
        algorithm_name=settings.jwt.algorithm
    )

    with Given(app, ['jwt', 'create']):
        assert stderr == ''
        token = f'{stdout}'[:-1]
        assert pirincipal.loads(token) == {}

        # Create a jwt token with a payload
        payload = dict(a=1)
        when(given + f'\'{json.dumps(payload)}\'')
        assert stderr == ''
        token = f'{stdout}'[:-1]
        assert pirincipal.loads(token) == payload

        # Create a expired token
        when(given + '-e -1')
        assert stderr == ''
        token = f'{stdout}'[:-1]
        with pytest.raises(SignatureExpired):
            pirincipal.loads(token)


if __name__ == '__main__':
    foo.cli_main(['jwt', 'create'])

