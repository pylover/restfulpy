
from restfulpy.cli.base import DatabaseLauncher


class CreateDatabaseLauncher(DatabaseLauncher):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('create-db', help="Create the server's database.")
        parser.add_argument('-d', '--drop', dest='drop_db', action='store_true', default=False,
                            help='Drop existing database before create another one.')
        parser.add_argument('-s', '--schema', dest='schema', action='store_true', default=False,
                            help='Creates database schema after creating the database.')
        parser.add_argument('-b', '--basedata', dest='basedata', action='store_true', default=False,
                            help='Implies `(-s|--schema)`, Inserts basedata after schema generation.')
        return parser

    def launch(self):
        from lemur.database.database_manager import DatabaseManager
        from lemur.models import setup_schema
        from lemur.database.basedata import insert_basedata

        with DatabaseManager() as db_admin:
            if self.args.drop_db:
                db_admin.drop_database()
            db_admin.create_database()
            if self.args.schema or self.args.basedata:
                setup_schema()
                if self.args.basedata:
                    insert_basedata()
