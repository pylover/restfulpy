import argparse
import sys

import argcomplete

from restfulpy.cli.admin import AdminLauncher
from restfulpy.cli.base import Launcher
from restfulpy.cli.migrate import MigrateLauncher
from restfulpy.cli.serve import ServeLauncher
from restfulpy.cli.worker import WorkerLauncher
from restfulpy.cli.dev import DevLauncher


class MainLauncher(Launcher):

    def __init__(self, application):
        self.application = application
        self.parser = parser = argparse.ArgumentParser(description='%s command line interface.' % application.name)
        parser.add_argument('-p', '--process-name', metavar="PREFIX", default=application.name,
                            help='A string indicates the logger prefix for this process, it helps to configure '
                                 'separate log files per process.')
        parser.add_argument('-c', '--config-file', metavar="FILE",
                            help='List of configuration files separated by space. Default: ""')
        parser.add_argument('-d', '--config-dir', metavar="DIR",
                            help='List of configuration directories separated by space. Default: ""')
        subparsers = parser.add_subparsers(title="sub commands", prog=application.name, dest="command")

        AdminLauncher.register(subparsers)
        ServeLauncher.register(subparsers)
        MigrateLauncher.register(subparsers)
        WorkerLauncher.register(subparsers)
        DevLauncher.register(subparsers)
        application.register_cli_launchers(subparsers)
        argcomplete.autocomplete(parser)

    def launch(self, args=None):

        if args:
            cli_args = self.parser.parse_args(args)
        else:
            cli_args = self.parser.parse_args()

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
