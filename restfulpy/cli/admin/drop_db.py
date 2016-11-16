
from restfulpy.cli.base import DatabaseLauncher


class DropDatabaseLauncher(DatabaseLauncher):

    @classmethod
    def create_parser(cls, subparsers):
        return subparsers.add_parser('drop-db', help="Setup the server's database.")

    def launch(self):
        from lemur.database.database_manager import DatabaseManager
        with DatabaseManager() as db_admin:
            db_admin.drop_database()
