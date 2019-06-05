import tempfile
from os import path

from bddcli import Given, stderr, Application, status, stdout, when, given

from restfulpy import Application as RestfulpyApplication


foo = RestfulpyApplication(name='Foo')


def foo_main():
    return foo.cli_main()


app = Application(
    'foo',
    'tests.test_appcli_configuration:foo_main'
)


def test_configuration_encrypt():

    with Given(app, 'configuration encrypt', stdin=b'abc'):
        assert stderr == b''
        assert status == 0
        assert stdout.startswith(b'#enc')
        binary = stdout.proxied_object
        when('configuration decrypt', stdin=binary)
        assert stderr == b''
        assert status == 0
        assert stdout == b'abc'


def test_configuration_dump():

    with Given(app, 'configuration dump'):
        assert stderr == ''
        assert status == 0
        assert len(stdout.proxied_object) > 100

        filename = tempfile.mktemp()
        when(given + filename)
        assert stderr == ''
        assert status == 0
        assert path.exists(filename)


if __name__ == '__main__': # pragma: no cover
    # Use for debugging
    foo.__configuration_cipher__ = None
    foo.cli_main(['configuration', 'encrypt'])
