import argparse

from restfulpy.cli import RequireSubCommand, Launcher
from restfulpy.db import DatabaseManager
from restfulpy.orm import setup_schema


class BasedataLauncher(Launcher):

    @classmethod
    def create_parser(cls, subparsers):
        return subparsers.add_parser(
            'basedata',
            help='Setup the server\'s database.'
        )

    def launch(self):
        self.args.application.insert_basedata()


class MockupDataLauncher(Launcher):

    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('mockup', help='Insert mockup data.')
        parser.add_argument('mockup_args', nargs=argparse.REMAINDER)
        return parser

    def launch(self):
        self.args.application.insert_mockup(self.args.mockup_args)


class CreateDatabaseLauncher(Launcher):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser(
            'create',
            help='Create the server\'s database.'
        )
        parser.add_argument(
            '-d',
            '--drop',
            dest='drop_db',
            action='store_true',
            default=False,
            help='Drop existing database before create another one.'
        )
        parser.add_argument(
            '-s',
            '--schema',
            dest='schema',
            action='store_true',
            default=False,
            help='Creates database schema after creating the database.'
        )
        parser.add_argument(
            '-b',
            '--basedata',
            action='store_true',
            default=False,
            help= \
                'Implies `(-s|--schema)`, Inserts basedata after schema '
                'generation.'
        )
        parser.add_argument(
            '-m',
            '--mockup',
            action='store_true',
            default=False,
            help='Implies `(-s|--schema)`, Inserts mockup data.'
        )
        return parser

    def launch(self):
        with DatabaseManager() as db_admin:
            if self.args.drop_db:
                db_admin.drop_database()
            db_admin.create_database()
            if self.args.schema or self.args.basedata or self.args.mockup:
                setup_schema()
                if self.args.basedata:
                    self.args.application.insert_basedata()
                if self.args.mockup:
                    self.args.application.insert_mockup()


class DropDatabaseLauncher(Launcher):

    @classmethod
    def create_parser(cls, subparsers):
        return subparsers.add_parser(
            'drop',
            help='Drop the server\'s database.'
        )

    def launch(self):
        with DatabaseManager() as db_admin:
            db_admin.drop_database()


class CreateDatabaseSchemaLauncher(Launcher):

    @classmethod
    def create_parser(cls, subparsers):
        return subparsers.add_parser(
            'schema',
            help='Creates the database objects.'
        )

    def launch(self):
        setup_schema()


class DatabaseLauncher(Launcher, RequireSubCommand):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('db', help='Database administrationn')
        admin_subparsers = parser.add_subparsers(
            title='admin command',
            dest='admin_command'
        )
        CreateDatabaseSchemaLauncher.register(admin_subparsers)
        BasedataLauncher.register(admin_subparsers)
        MockupDataLauncher.register(admin_subparsers)
        DropDatabaseLauncher.register(admin_subparsers)
        CreateDatabaseLauncher.register(admin_subparsers)
        return parser

