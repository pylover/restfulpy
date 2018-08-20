import os
import sys
from os.path import join, basename, abspath

from .launchers import Launcher, RequireSubCommand


def print_venv_restart_help():
    venv = basename(os.environ['VIRTUAL_ENV'])
    print('\nPlease run this to apply changes auto completion:\n')
    print(f'    deactivate && workon {venv}\n')


class AutoCompletionLauncher(Launcher, RequireSubCommand):

    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser(
            'autocompletion',
            help='Bash autocompletion management'
        )
        sub_subparsers = parser.add_subparsers(dest='autocompletion_command')
        AutoCompletionInstaller.register(sub_subparsers)
        AutoCompletionUninstaller.register(sub_subparsers)
        return parser


class AutoCompletionInstaller(Launcher):

    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('install')
        parser.add_argument(
            '-s', '--system-wide',
            action='store_true',
            help=f'Add the PYTHON_ARGCOMPLETE_OK into first 1024 bytes of the  {sys.argv[0]}'
        )
        return parser

    def launch(self):
        if 'VIRTUAL_ENV' in os.environ:
            if self.args.system_wide:
                print(
                    'The -s/--system-wide flag can not be used within virtualenv',
                    file=sys.stderr
                )
                return 1
            self.install_virtualenv()
        elif self.args.system_wide:
            self.install_systemwide()
        else:
            self.install_user()

    def install_virtualenv(self):
        sourcefile = join(os.environ['VIRTUAL_ENV'], 'bin/postactivate')
        result = self.install_file(sourcefile)
        if not result:
            print_venv_restart_help()
        return result

    def install_user(self):
        sourcefile = join(os.environ['HOME'], '.bashrc')
        return self.install_file(sourcefile)

    def install_file(self, filename):
        line = 'eval "$(register-python-argcomplete %s)"\n' % basename(sys.argv[0])

        with open(filename) as f:
            content = f.readlines()

        if line in content:
            print(
                'The autocompletion is already activated.\n'
                f'it means the line:\n\n    {line}\nwas found in file {abspath(filename)}',
                file=sys.stderr
            )
            return 1

        with open(filename, mode='a') as f:
            f.write(line)

        print(f'The line:\n\n    {line}\nwas added into {abspath(filename)}')

    def install_systemwide(self):
        line = '# PYTHON_ARGCOMPLETE_OK'
        filename = sys.argv[0]
        with open(filename) as f:

            content = f.read(1024)
            if line in content:
                print(
                    'The autocompletion is already activated.\n'
                    f'it means the line:\n\n    '
                    f'{line}\nwas found in file {abspath(filename)}',
                    file=sys.stderr
                )
                return 1

            content += f.read()

        lines = content.splitlines()
        lines.insert(1, line)
        with open(filename, mode='w') as f:
            for l in lines:
                f.write(f'{l}\n')

        print(f'The line: {line} was added into: {abspath(filename)}')


class AutoCompletionUninstaller(Launcher):

    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('uninstall')
        parser.add_argument(
            '-s', '--system-wide',
            action='store_true',
            help=f'Remove the PYTHON_ARGCOMPLETE_OK from {sys.argv[0]}'
        )
        return parser

    def launch(self):
        if 'VIRTUAL_ENV' in os.environ:
            if self.args.system_wide:
                print(
                    'The -s/--system-wide flag can not be used within ',
                    'virtualenv',
                    file=sys.stderr
                )
                return 1
            self.uninstall_from_virtualenv()
        elif self.args.system_wide:
            self.uninstall_systemwide()
        else:
            self.uninstall_from_user()

    def uninstall_from_virtualenv(self):
        sourcefile = join(os.environ['VIRTUAL_ENV'], 'bin/postactivate')
        result = self.uninstall_from_file(sourcefile)
        if not result:
            print_venv_restart_help()
        return result

    def uninstall_from_user(self):
        sourcefile = join(os.environ['HOME'], '.bashrc')
        return self.uninstall_from_file(sourcefile)

    def uninstall_from_file(self, filename):
        line = \
            f'eval "$(register-python-argcomplete {basename(sys.argv[0])})"\n'
        return self.remove_line_from_file(filename, line)

    def uninstall_systemwide(self):
        line = '# PYTHON_ARGCOMPLETE_OK\n'
        filename = sys.argv[0]
        self.remove_line_from_file(filename, line)

    def remove_line_from_file(self, filename, line):
        with open(filename) as f:
            lines = f.readlines()

        found = False
        with open(filename, mode='w') as f:
            for l in lines:
                if line != l:
                    f.write(l)
                else:
                    found = True

        if found:
            print(
                f'The line:\n\n    '
                f'{line}\nwas removed from {abspath(filename)}'
            )
        else:
            print(
                'The autocompletion is already deactivated.\n'
                f'it means the line:\n\n'
                '    {line}\nwas not found in file {abspath(filename)}',
                file=sys.stderr
            )
            return 1

