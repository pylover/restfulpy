
from os.path import join
import argparse

from alembic.config import main as alembic_main

from restfulpy.cli.base import Launcher


class MigrateLauncher(Launcher):

    @classmethod
    def create_parser(cls, subparsers):
        migrate_parser = subparsers.add_parser('migrate', help="Executes the alembic command")
        migrate_parser.add_argument('alembic_args', nargs=argparse.REMAINDER,
                                    help="For more information, please see `alembic --help`")
        return migrate_parser

    def launch(self):
        alembic_ini = join(self.args.application.root_path, 'alembic.ini')
        alembic_main(argv=['--config', alembic_ini] + self.args.alembic_args)
