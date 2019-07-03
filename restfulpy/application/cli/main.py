import sys
from os.path import basename

from easycli import Root, Argument

from .configuration import ConfigurationSubCommand
from .database import DatabaseSubCommand
from .jwttoken import JWTSubCommand
from .migrate import MigrateSubCommand
from .worker import WorkerSubCommand
from .mule import MuleSubCommand


class EntryPoint(Root):
    __completion__ = True
    __arguments__ = [
        Argument(
            '-V', '--version',
            action='store_true',
            help='Show application version',
        ),
        Argument(
            '-p', '--process-name',
            metavar="PREFIX",
            default=basename(sys.argv[0]),
            help='A string indicates the name for this process.',
        ),
        Argument(
            '-c', '--config-file',
            metavar="FILE",
            help='Configuration file, Default: none',
        ),
        ConfigurationSubCommand,
        DatabaseSubCommand,
        JWTSubCommand,
        MigrateSubCommand,
        WorkerSubCommand,
        MuleSubCommand,
    ]

    def __init__(self, application):
        self.application = application
        self.__command__ = application.name
        self.__help__ = '%s command line interface.' % application.name
        extra_arguments = self.application.get_cli_arguments()
        if extra_arguments is not None:
            self.__arguments__.extend(extra_arguments)
        super().__init__()

    def _execute_subcommand(self, args):
        args.application = self.application
        self.application.process_name = args.process_name
        self.application.configure(filename=args.config_file)
        self.application.initialize_orm()
        return super()._execute_subcommand(args)

    def __call__(self, args):
        if args.version:
            print(self.application.version)
            return

        return super().__call__(args)

