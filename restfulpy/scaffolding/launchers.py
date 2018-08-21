import os
import sys
from os import path

from nanohttp import quickstart

from restfulpy.cli import Launcher
from restfulpy.utils import to_pascal_case
import restfulpy


DEFAULT_ADDRESS = '8080'
HERE = path.dirname(__file__)
TEMPLATES_PATH = path.abspath(path.join(HERE, 'templates'))


class ScaffoldLauncher(Launcher):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser(
            'scaffold',
            help='Creates an empty boilerplate'
        )
        parser.add_argument(
            'name',
            help='The snake_case project\'s name'
        )
        parser.add_argument(
            'author',
            help='The project\'s author'
        )
        parser.add_argument(
            'email',
            help='The projects author\'s email'
        )
        parser.add_argument(
            '-t',
            '--template',
            default='full',
            help= \
                'The project\'s template, one of (full, simple, singlefile). '
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
        template_path = path.join(TEMPLATES_PATH, self.args.template)
        target_path = path.abspath(self.args.directory)
        title_snakecase = self.args.name.lower()

        if not path.exists(template_path):
            print(f'Invalid template: {template_path}', file=sys.stderr)
            return 1

        if not path.exists(target_path):
            print(f'Invalid target path: {target_path}', file=sys.stderr)
            return 1

        for top, subdirectories, subfiles in os.walk(template_path):
            current_directory = path.relpath(top, template_path) \
                .replace('__project__', title_snakecase)
            for filename in subfiles:
                if not filename.endswith('.template'):
                    continue

                source = path.abspath(path.join(top, filename))
                target = path.abspath(path.join(
                    target_path,
                    current_directory,
                    filename[:-9].replace('__project__', title_snakecase)
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
        title_snakecase = self.args.name.lower()
        title_camelcase = to_pascal_case(title_snakecase)

        with open(source) as s, open(target, 'w') as t:
            content = s.read()
            content = content.replace('${project_snakecase}', title_snakecase)
            content = content.replace('${project_author}', self.args.author)
            content = content.replace(
                '${project_author_email}',
                self.args.email
            )
            content = content.replace(
                '${project_camelcase}',
                title_camelcase,
            )
            content = content.replace(
                '${restfulpy_version}',
                restfulpy.__version__
            )
            t.write(content)

