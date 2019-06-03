import sys

import yaml
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


class ConfigurationEncrptorSubSubCommand(SubCommand):
    __command__ = 'encrypt'
    __help__ = 'Encrypt configu file'

    def __call__(self, args):
        sys.stdout.buffer.write(b'#enc')
        sys.stdout.buffer.write(
            args.application.__configuration_cipher__.encrypt(
                sys.stdin.buffer.read()
            )
        )


class ConfigurationDecryptorSubSubCommand(SubCommand):
    __command__ = 'decrypt'
    __help__ = 'Decrypt the config file'

    def __call__(self, args):
        sys.stdout.buffer.write(
            args.application.__configuration_cipher__.decrypt(
                sys.stdin.buffer.read().lstrip(b'#enc')
            )
        )


class ConfigurationSubCommand(SubCommand):
    __command__ = 'configuration'
    __help__ = 'Configuration tools'
    __arguments__ = [
        ConfigurationDumperSubSubCommand,
        ConfigurationEncrptorSubSubCommand,
        ConfigurationDecryptorSubSubCommand,
    ]

