
from restfulpy.cli.base import DatabaseLauncher


class SetupDatabaseLauncher(DatabaseLauncher):

    @classmethod
    def create_parser(cls, subparsers):
        return subparsers.add_parser('setup-db', help="Setup the server's database.")

    def launch(self):
        from lemur.models import setup_schema
        setup_schema()
