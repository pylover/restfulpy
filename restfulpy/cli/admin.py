from logging import NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL

from restfulpy.cli.base import RequireSubCommand, Launcher
from restfulpy.db import DatabaseManager
from restfulpy.orm import setup_schema
from restfulpy.logging_ import get_logger


class BasedataLauncher(Launcher):

    @classmethod
    def create_parser(cls, subparsers):
        return subparsers.add_parser('base-data', help="Setup the server's database.")

    def launch(self):
        self.args.application.insert_basedata()


class MockupDataLauncher(Launcher):

    @classmethod
    def create_parser(cls, subparsers):
        return subparsers.add_parser('mockup-data', help="Insert mockup data.")

    def launch(self):
        self.args.application.insert_mockup()


class CreateDatabaseLauncher(Launcher):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('create-db', help="Create the server's database.")
        parser.add_argument('-d', '--drop', dest='drop_db', action='store_true', default=False,
                            help='Drop existing database before create another one.')
        parser.add_argument('-s', '--schema', dest='schema', action='store_true', default=False,
                            help='Creates database schema after creating the database.')
        parser.add_argument('-b', '--basedata', action='store_true', default=False,
                            help='Implies `(-s|--schema)`, Inserts basedata after schema generation.')
        parser.add_argument('-m', '--mockup', action='store_true', default=False,
                            help='Implies `(-s|--schema, -b|--basedata)`, Inserts mockup data.')
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
        return subparsers.add_parser('drop-db', help="Setup the server's database.")

    def launch(self):
        with DatabaseManager() as db_admin:
            db_admin.drop_database()


class SetupDatabaseLauncher(Launcher):

    @classmethod
    def create_parser(cls, subparsers):
        return subparsers.add_parser('setup-db', help="Setup the server's database.")

    def launch(self):
        setup_schema()

log_levels = {
    'notset': NOTSET,       # 0
    'debug': DEBUG,         # 10
    'info': INFO,           # 20
    'warning': WARNING,     # 30
    'error': ERROR,         # 40
    'critical': CRITICAL    # 50
}


class LogLauncher(Launcher):

    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('log', help="Setup the server's database.")
        parser.add_argument('message', nargs='+', help='The log message')
        parser.add_argument('-g', '--logger', default='main', help='The logger name, default: main')
        parser.add_argument('-l', '--level', default='debug', help='Log level, default info')
        return parser

    def launch(self):
        getattr(get_logger(self.args.logger), self.args.level)(' '.join(self.args.message))


class AdminLauncher(Launcher, RequireSubCommand):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('admin', help="Administrate the application")
        admin_subparsers = parser.add_subparsers(title="admin command", dest="admin_command")
        SetupDatabaseLauncher.register(admin_subparsers)
        BasedataLauncher.register(admin_subparsers)
        MockupDataLauncher.register(admin_subparsers)
        DropDatabaseLauncher.register(admin_subparsers)
        CreateDatabaseLauncher.register(admin_subparsers)
        LogLauncher.register(admin_subparsers)
        return parser
