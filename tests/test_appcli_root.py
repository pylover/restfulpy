from bddcli import Given, given, when, stdout, stderr, Application, status

from restfulpy import Application as RestfulpyApplication


foo = RestfulpyApplication(name='Foo')
app = Application('foo', 'tests.test_appcli_jwt:foo.cli_main')


def test_appcli_root():
    with Given(app):
        assert stderr == ''
        assert status == 0
        assert stdout == EXPECTED_HELP


EXPECTED_HELP = '''\
usage: foo [-h] [-p PREFIX] [-c FILE]
           {configuration,db,jwt,migrate,worker,completion} ...

optional arguments:
  -h, --help            show this help message and exit
  -p PREFIX, --process-name PREFIX
                        A string indicates the name for this process.
  -c FILE, --config-file FILE
                        Configuration file, Default: none

Sub commands:
  {configuration,db,jwt,migrate,worker,completion}
    configuration       Configuration tools
    db                  Database administrationn
    jwt                 JWT management
    migrate             Executes the alembic command
    worker              Task queue administration
    completion          Bash auto completion using argcomplete python package.
'''


if __name__ == '__main__':  # pragma: no cover
    foo.cli_main([])

