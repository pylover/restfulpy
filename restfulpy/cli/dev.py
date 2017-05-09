
import yaml
from nanohttp import settings
from restfulpy.cli.base import RequireSubCommand, Launcher


class EmailLauncher(Launcher):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('email', help="Sends a test email")
        parser.add_argument('target')
        parser.add_argument('-m', '--message', default='The email body')
        parser.add_argument('-s', '--subject', default='Test subject')
        parser.add_argument('-f', '--from', dest='from_', default='restfulpy@example.com')
        return parser

    def launch(self):
        from restfulpy.messaging import SmtpProvider

        p = SmtpProvider()
        p.send(self.args.target, self.args.subject, self.args.message, from_=self.args.from_)


class LogLauncher(Launcher):

    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('log', help="Setup the server's database.")
        parser.add_argument('message', nargs='+', help='The log message')
        parser.add_argument('-g', '--logger', default='main', help='The logger name, default: main')
        parser.add_argument('-l', '--level', default='debug', help='Log level, default info')
        return parser

    def launch(self):
        from restfulpy.logging_ import get_logger

        getattr(get_logger(self.args.logger), self.args.level)(' '.join(self.args.message))


class ConfigurationDumpLauncher(Launcher):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('config-dump', help="Dump the configuration")
        parser.add_argument('path', help='The config path, for example: db')
        return parser

    def launch(self):
        dump = yaml.dump(getattr(settings, self.args.path), default_flow_style=False)
        print(dump)


class DevLauncher(Launcher, RequireSubCommand):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('dev', help="Development commands")
        dev_subparsers = parser.add_subparsers(title="admin command", dest="admin_command")
        LogLauncher.register(dev_subparsers)
        EmailLauncher.register(dev_subparsers)
        ConfigurationDumpLauncher.register(dev_subparsers)
        return parser
