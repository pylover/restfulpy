from bddcli import Given, stderr, Application, status
from restfulpy import Application as RestfulpyApplication


foo = RestfulpyApplication(name='migration')


def foo_main():
    return foo.cli_main()


app = Application('foo', 'tests.test_appcli_migrate:foo_main')


def test_migrate():
    with Given(app, 'migrate'):
        assert stderr.startswith('usage: foo')
        assert status == 2


if __name__ == '__main__':  # pragma: no cover
    foo.cli_main(['migrate', '--help'])

