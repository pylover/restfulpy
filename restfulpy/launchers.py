import sys
import argparse
from os import path

import argcomplete

from .cli import Launcher, AutoCompletionLauncher


class RestfulpyMainLauncher(Launcher):

    def __init__(self):
        self.parser = parser = argparse.ArgumentParser(
            description='Restfulpy command line interface.'
        )
        subparsers = parser.add_subparsers(
            title='Restfulpy sub commands',
            prog=path.basename('restfulpy'),
            dest='command'
        )

        AutoCompletionLauncher.register(subparsers)

        from .scaffolding.launchers import ScaffoldLauncher
        ScaffoldLauncher.register(subparsers)

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

