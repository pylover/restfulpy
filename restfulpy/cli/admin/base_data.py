
from restfulpy.cli.base import DatabaseLauncher


class BasedataLauncher(DatabaseLauncher):

    @classmethod
    def create_parser(cls, subparsers):
        return subparsers.add_parser('base-data', help="Setup the server's database.")

    def launch(self):
        self.args.application.insert_basedata()
