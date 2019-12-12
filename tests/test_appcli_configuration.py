import tempfile
from os import path

from bddcli import Given, stderr, Application, status, stdout, when, given

from restfulpy import Application as RestfulpyApplication


foo = RestfulpyApplication(name='Foo')
app = Application('foo', 'tests.test_appcli_configuration:foo.cli_main')


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

