import base64
import json

from bddcli import Given, given, when, stdout, stderr, Application, status

from restfulpy import Application as RestfulpyApplication


foo = RestfulpyApplication(name='jwt')


def foo_main():
    return foo.cli_main()


app = Application('foo', 'tests.test_appcli_jwt:foo_main')


def test_jwt():
    with Given(app, 'jwt create'):
        assert stderr == ''
        assert status == 0
        assert len(stdout) > 10

        when(given + '\'{"foo": 1}\'')
        assert stderr == ''
        assert status == 0
        header, payload, signature = stdout.encode().split(b'.')
        payload = base64.urlsafe_b64decode(payload)
        assert json.loads(payload) == {'foo': 1}


if __name__ == '__main__':  # pragma: no cover
    foo.cli_main(['jwt', 'create', '{"foo": 1}'])

