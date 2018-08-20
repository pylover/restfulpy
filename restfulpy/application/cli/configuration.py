import sys

from restfulpy.cli import RequireSubCommand, Launcher


class ConfigurationLauncher(Launcher, RequireSubCommand):

    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser(
            'configuration',
            help='Configuration tools'
        )
        subparsers = parser.add_subparsers(
            title='configuration command',
            dest='config_command'
        )
        EncryptConfigurationLauncher.register(subparsers)
        DecryptConfigurationLauncher.register(subparsers)
        return parser


class EncryptConfigurationLauncher(Launcher):

    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('encrypt', help='Encrypt configu file')
        return parser

    def launch(self):
        sys.stdout.buffer.write(b'#enc')
        sys.stdout.buffer.write(
        self.args.application.__configuration_cipher__.encrypt(
            sys.stdin.buffer.read()
        ))


class DecryptConfigurationLauncher(Launcher):

    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser(
            'decrypt',
            help='Decrypt the config file'
        )
        return parser

    def launch(self):
        sys.stdout.buffer.write(
            self.args.application.__configuration_cipher__.decrypt(
                sys.stdin.buffer.read().lstrip(b'#enc')
            )
        )

