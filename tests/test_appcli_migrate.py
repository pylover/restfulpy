from bddcli import Given, stderr, Application, status
from restfulpy import Application as RestfulpyApplication


foo = RestfulpyApplication(name='migration')
app = Application('foo', 'tests.test_appcli_migrate:foo.cli_main')


def test_migrate():
    with Given(app, 'migrate'):
        assert stderr.startswith('usage: foo')
        assert status == 2


if __name__ == '__main__':  # pragma: no cover
    foo.cli_main(['migrate', '--help'])

