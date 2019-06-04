import argparse
import os
from os.path import join

from alembic.config import main as alembic_main
from easycli import SubCommand, Argument


class MigrateSubCommand(SubCommand):
    __command__ = 'migrate'
    __help__ = 'Executes the alembic command'
    __arguments__ = [
        Argument(
            'alembic_args',
            nargs=argparse.REMAINDER,
            help='For more information, please see `alembic --help`',
        ),
    ]

    def __call__(self, args):
        current_directory = os.curdir
        try:
            os.chdir(args.application.root_path)
            alembic_ini = join(args.application.root_path, 'alembic.ini')
            alembic_main(argv=['--config', alembic_ini] + args.alembic_args)

        finally:
            os.chdir(current_directory)

