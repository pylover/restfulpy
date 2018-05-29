import argparse
import sys
import warnings
from os.path import basename
import argcomplete


from .application import Application
from .cli import Launcher


warnings.filterwarnings('ignore', message='Unknown REQUEST_METHOD')


__version__ = '0.49.3'


class RestfulpyMainLauncher(Launcher):

    def __init__(self):
        self.parser = parser = argparse.ArgumentParser(
            prog='restfulpy',
            description='Restfulpy command line interface.'
        )
        subparsers = parser.add_subparsers(
            title="Restfulpy sub commands",
            prog=basename(sys.argv[0]),
            dest="command"
        )

        from restfulpy.mockupservers import SimpleMockupServerLauncher
        SimpleMockupServerLauncher.register(subparsers)

        from restfulpy.documentary import DocumentaryLauncher
        DocumentaryLauncher.register(subparsers)

        argcomplete.autocomplete(parser)

    def launch(self, args=None):
        cli_args = self.parser.parse_args(args if args else None)
        if hasattr(cli_args, 'func'):
            cli_args.func(cli_args)
        else:
            self.parser.print_help()
        sys.exit(0)

    @classmethod
    def create_parser(cls, subparsers):
        """
        Do nothing here
        """
        pass


def main():
    RestfulpyMainLauncher()()
