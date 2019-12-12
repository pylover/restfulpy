import sys
from os.path import basename

from easycli import Root, Argument

from .configuration import ConfigurationSubCommand
from .database import DatabaseSubCommand
from .jwttoken import JWTSubCommand
from .migrate import MigrateSubCommand
from .worker import WorkerSubCommand


class EntryPoint(Root):
    __completion__ = True
    __arguments__ = [
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
    ]

    def __init__(self, application):
        self.application = application
        self.__command__ = application.name
        self.__help__ = '%s command line interface.' % application.name
        self.__arguments__.extend(self.application.__cli_arguments__)
        super().__init__()

    def _execute_subcommand(self, args):
        args.application = self.application
        self.application.name = args.process_name
        self.application.configure(filename=args.config_file)
        self.application.initialize_orm()
        return super()._execute_subcommand(args)

