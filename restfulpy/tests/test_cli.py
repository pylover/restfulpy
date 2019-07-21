import time

from bddcli import Given, stderr, Application, status, when, story, \
    given, stdout

import restfulpy
from restfulpy import Application as RestfulpyApplication
from restfulpy.taskqueue import RestfulpyTask


app = Application('restfulpy', 'restfulpy.cli:main')


def test_restfulpy_cli(db):
    with Given(app):
        assert stdout.startswith('usage')
        assert status == 0

        when(given + '--version')
        assert stdout == f'{restfulpy.__version__}\n'
        assert status == 0


if __name__ == '__main__':  # pragma: no cover
    foo.cli_main(['migrate', '--help'])

