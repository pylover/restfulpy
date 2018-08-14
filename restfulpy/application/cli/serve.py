from nanohttp import quickstart

from restfulpy.cli import Launcher


DEFAULT_ADDRESS = '8080'


class ServeLauncher(Launcher):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser(
            'serve',
            help="Serves the application on http."
        )
        parser.add_argument(
            '-b',
            '--bind',
            default=DEFAULT_ADDRESS, metavar='{HOST:}PORT',
            help='Bind Address. default: %s' % DEFAULT_ADDRESS
        )
        return parser

    def launch(self):
        host, port = \
            self.args.bind.split(':') if ':' in self.args.bind \
            else ('', self.args.bind)

        quickstart(
            application=self.args.application,
            host=host,
            port=port
        )
