
from ..cli import Launcher, RequireSubCommand


class DocumentaryLauncher(Launcher, RequireSubCommand):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('documentary', help='Documentary tools')
        documentary_subparsers = parser.add_subparsers(title='documentary command', dest='documentary_command')
        DocumentGeneratorLauncher.register(documentary_subparsers)
        return parser


class DocumentGeneratorLauncher(Launcher):
    __command__ = 'generate'

    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser(cls.__command__, help='Generates the documentation from yaml test specs')
        parser.add_argument('output-directory', help='Path to the directory to store generated files')
        parser.add_argument(
            '-d', '--input-directory',
            default='.',
            help='Path to the directory which contains the test spec yaml(*.yml) files. '
                 'if omitted, the current directory will be used'
        )
        parser.add_argument(
            '-f', '--format',
            default='md',
            help='The output format, supported formats: md'
        )
        return parser

    def launch(self):
        from .formatters import MarkdownFormatter
        formatter = MarkdownFormatter()
        formatter.load(self.args.input_directory)
        formatter.dump(self.args.output_directory)
