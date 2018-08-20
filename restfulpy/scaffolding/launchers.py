from nanohttp import quickstart

from restfulpy.cli import Launcher


DEFAULT_ADDRESS = '8080'


class ScaffoldLauncher(Launcher):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser(
            'scaffold',
            help='Creates an empty boilerplate'
        )
        parser.add_argument(
            'name',
            help='The project\'s name'
        )
        return parser

    def launch(self):
        print(self.args.name)

