from lemur.cli.admin.create_db import CreateDatabaseLauncher
from lemur.cli.admin.drop_db import DropDatabaseLauncher
from lemur.cli.admin.reset_password import ResetPasswordLauncher
from lemur.cli.admin.setup_db import SetupDatabaseLauncher
from lemur.cli.base import Launcher, RequireSubCommand
from restfulpy.cli.admin.base_data import BasedataLauncher


class AdminLauncher(Launcher, RequireSubCommand):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('admin', help="Administrate the application")
        admin_subparsers = parser.add_subparsers(title="admin command", dest="admin_command")
        SetupDatabaseLauncher.register(admin_subparsers)
        BasedataLauncher.register(admin_subparsers)
        DropDatabaseLauncher.register(admin_subparsers)
        CreateDatabaseLauncher.register(admin_subparsers)
        ResetPasswordLauncher.register(admin_subparsers)
        return parser
