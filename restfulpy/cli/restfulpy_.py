import sys
import argparse

import argcomplete

from .base import Launcher
from ..testing.mockup.restfulpy_ import MockupServerLauncher


class RestfulpyMainLauncher(Launcher):

    def __init__(self):
        self.parser = parser = argparse.ArgumentParser(description='Restfulpy command line interface.')
        subparsers = parser.add_subparsers(title="Restfulpy sub commands", prog=sys.argv[0], dest="command")
        MockupServerLauncher.register(subparsers)
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
