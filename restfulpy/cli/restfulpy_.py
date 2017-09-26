import sys
import argparse

from .base import Launcher
from ..configuration import configure


class RestfulpyMainLauncher(Launcher):

    def __init__(self):
        self.parser = parser = argparse.ArgumentParser(description='Restfulpy command line interface.')
        parser.add_argument('-c', '--config-file', metavar="FILE",
                            help='List of configuration files separated by space. Default: ""')
        subparsers = parser.add_subparsers(title="sub commands", prog=sys.argv[0], dest="command")

        MockupServerLauncher.register(subparsers)
        argcomplete.autocomplete(parser)

    def launch(self, args=None):

        if args:
            cli_args = self.parser.parse_args(args)
        else:
            cli_args = self.parser.parse_args()

        configure(files=cli_args.config_file)
        cli_args.application = self.application
        self.application.process_name = cli_args.process_name
        self.application.configure(files=cli_args.config_file)
        self.application.initialize_models()
        cli_args.func(cli_args)
        sys.exit(0)

    @classmethod
    def create_parser(cls, subparsers):
        """
        Do nothing here
        """
        pass