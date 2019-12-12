import sys

from easycli import SubCommand, Argument
from nanohttp import settings


class ConfigurationDumperSubSubCommand(SubCommand):
    __command__ = 'dump'
    __help__ = 'Dump the configuration'
    __arguments__ = [
        Argument(
            'path',
            nargs='?',
            help='The config path, for example: db, stdout if omitted',
        ),
    ]

    def __call__(self, args):
        dump = settings.dumps()
        if args.path:
            with open(args.path, 'w') as f:
                f.write(dump)
        else:
            print(dump)


class ConfigurationSubCommand(SubCommand):
    __command__ = 'configuration'
    __help__ = 'Configuration tools'
    __arguments__ = [
        ConfigurationDumperSubSubCommand,
    ]

