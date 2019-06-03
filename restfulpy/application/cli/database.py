import argparse

from easycli import SubCommand, Argument

from restfulpy.db import PostgreSQLManager as DBManager
from restfulpy.orm import setup_schema


class BasedataSubSubCommand(SubCommand):
    __command__ = 'basedata'
    __help__ = 'Setup the server\'s database.'

    def __call__(self, args):
        args.application.insert_basedata()


class MockupDataSubSubCommand(SubCommand):
    __command__ = 'mockup'
    __help__ = 'Insert mockup data.'
    __arguments__ = [
        Argument(
            'mockup_args',
            nargs=argparse.REMAINDER,
        ),
    ]

    def __call__(self, args):
        args.application.insert_mockup(args.mockup_args)


class CreateDatabaseSubSubCommand(SubCommand):
    __command__ = 'create'
    __help__ = 'Create the server\'s database.'
    __arguments__ = [
        Argument(
            '-d',
            '--drop',
            dest='drop_db',
            action='store_true',
            default=False,
            help='Drop existing database before create another one.',
        ),
        Argument(
            '-s',
            '--schema',
            dest='schema',
            action='store_true',
            default=False,
            help='Creates database schema after creating the database.',
        ),
        Argument(
            '-b',
            '--basedata',
            action='store_true',
            default=False,
            help='Implies `(-s|--schema)`, Inserts basedata after schema' \
                'generation.',
        ),
        Argument(
            '-m',
            '--mockup',
            action='store_true',
            default=False,
            help='Implies `(-s|--schema)`, Inserts mockup data.',
        ),
    ]

    def __call__(self, args):
        with DBManager() as db_admin:
            if args.drop_db:
                db_admin.drop_database()

            db_admin.create_database()
            if args.schema or args.basedata or args.mockup:
                setup_schema()
                if args.basedata:
                    args.application.insert_basedata()

                if args.mockup:
                    args.application.insert_mockup()


class DropDatabaseSubSubCommand(SubCommand):
    __command__ = 'drop'
    __help__ = 'Drop the server\'s database.'

    def __call__(self, args):
        with DBManager() as db_admin:
            db_admin.drop_database()


class CreateDatabaseSchemaSubSubCommand(SubCommand):
    __command__ = 'schema'
    __help__ = 'Creates the database objects.'

    def __call__(self, args):
        setup_schema()


class DatabaseSubCommand(SubCommand):
    __command__ = 'db'
    __help__ = 'Database administrationn'
    __arguments__ = [
        CreateDatabaseSchemaSubSubCommand,
        BasedataSubSubCommand,
        MockupDataSubSubCommand,
        DropDatabaseSubSubCommand,
        CreateDatabaseSubSubCommand,
    ]

