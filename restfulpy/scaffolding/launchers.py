import os
import sys
from os import path

from nanohttp import quickstart

from restfulpy.cli import Launcher
import restfulpy


DEFAULT_ADDRESS = '8080'
HERE = path.dirname(__file__)


class ScaffoldLauncher(Launcher):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser(
            'scaffold',
            help='Creates an empty boilerplate'
        )
        parser.add_argument(
            'name',
            help='The project\'s name'
        )
        parser.add_argument(
            'author',
            help='The project\'s author'
        )
        parser.add_argument(
            '-t',
            '--template',
            default='full',
            help= \
                'The project\'s template, one of (full, singlefile). '
                'default: full.'
        )
        parser.add_argument(
            '-o',
            '--overwrite',
            default=False,
            action='store_true',
            help= \
                'Continue and overwrite files when the target '
                'directory(-d/--directory) is not empty.'
        )
        parser.add_argument(
            '-d',
            '--directory',
            default='.',
            help= \
                'Change to this directory before generating new files. '
                'default: "."'
        )

        return parser

    def launch(self):
        template_path = path.abspath(
            path.join(HERE, 'templates', self.args.template)
        )
        target_path = path.abspath(self.args.directory)

        if not path.exists(template_path):
            print(f'Invalid template: {template_path}', file=sys.stderr)
            return 1

        if not path.exists(target_path):
            print(f'Invalid target path: {target_path}', file=sys.stderr)
            return 1

        for top, subdirectories, subfiles in os.walk(template_path):
            current_directory = path.relpath(top, template_path) \
                .replace('__project__', self.args.name)
            for filename in subfiles:
                if not filename.endswith('.template'):
                    continue

                source = path.abspath(path.join(top, filename))
                target = path.abspath(path.join(
                    target_path,
                    current_directory,
                    filename[:-9].replace('__project__', self.args.name)
                ))
                if not self.args.overwrite and path.exists(target):
                    print(
                        f'Target file exists: {target}, use -o to overwrite',
                        file=sys.stderr
                    )
                    return 1

                os.makedirs(path.dirname(target), exist_ok=True)
                self.install_file(source, target)

    def install_file(self, source, target):
        print(f'Installing  {target}')

        with open(source) as s, open(target, 'w') as t:
            content = s.read()
            content = content.replace('${project_name}', self.args.name)
            content = content.replace('${project_author}', self.args.author)
            content = content.replace(
                '${project_title}',
                self.args.name.capitalize()
            )
            content = content.replace(
                '${restfulpy_version}',
                restfulpy.__version__
            )
            t.write(content)

