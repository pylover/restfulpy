import sys

from easycli import SubCommand, Argument


class ConfigurationDumperSubSubCommand(SubCommand):
    __command__ = 'dump'
    __help__ = 'Dump the configuration'
    __arguments__ = [
        Argument(
            'path',
            help='The config path, for example: db',
        ),
    ]

    def __call__(self, args):
        dump = yaml.dump(
            getattr(settings, args.path),
            default_flow_style=False
        )
        print(dump)


class ConfigurationEncrptorSubSubCommand(SubCommand):
    __command__ = 'encrypt'
    __help__ = 'Encrypt configu file'

    def __call__(self, args):
        if args.application.__configuration_cipher__ is not None:
            sys.stdout.buffer.write(b'#enc')
            sys.stdout.buffer.write(
                args.application.__configuration_cipher__.encrypt(
                    sys.stdin.buffer.read()
                )
            )

        else:
            sys.stdout.buffer.write(b'The configuration cipher not set.\n')


class ConfigurationDecryptorSubSubCommand(SubCommand):
    __command__ = 'decrypt'
    __help__ = 'Decrypt the config file'

    def __call__(self, args):
        if args.application.__configuration_cipher__ is not None:
            sys.stdout.buffer.write(
                args.application.__configuration_cipher__.decrypt(
                    sys.stdin.buffer.read().lstrip(b'#enc')
                )
            )

        else:
            sys.stdout.buffer.write(b'The configuration cipher not set.\n')


class ConfigurationSubCommand(SubCommand):
    __command__ = 'configuration'
    __help__ = 'Configuration tools'
    __arguments__ = [
        ConfigurationDumperSubSubCommand,
        ConfigurationEncrptorSubSubCommand,
        ConfigurationDecryptorSubSubCommand,
    ]

