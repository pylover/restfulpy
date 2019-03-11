import os
import sys
from os import path

from easycli import SubCommand, Argument

import restfulpy
from restfulpy.utils import to_pascal_case


DEFAULT_ADDRESS = '8080'
HERE = path.dirname(__file__)
TEMPLATES_PATH = path.abspath(path.join(HERE, 'templates'))
TEMPLATES = [
    d for d in os.listdir(TEMPLATES_PATH)
    if path.isdir(path.join(TEMPLATES_PATH, d)) and d[0] not in ('.', '_')
]


class ScaffoldSubCommand(SubCommand):
    __command__ = 'scaffold'
    __help__ = 'Creates an empty boilerplate'
    __arguments__ = [
        Argument(
            'name',
            help='The snake_case project\'s name'
        ),
        Argument(
            'author',
            help='The project\'s author'
        ),
        Argument(
            'email',
            help='The projects author\'s email'
        ),
        Argument(
            '-t',
            '--template',
            default='full',
            help= \
                f'The project\'s template, one of {", ".join(TEMPLATES)}. '
                f'default: full.'
        ),
        Argument(
            '-o',
            '--overwrite',
            default=False,
            action='store_true',
            help= \
                'Continue and overwrite files when the target '
                'directory(-d/--directory) is not empty.'
        ),
        Argument(
            '-d',
            '--directory',
            default='.',
            help= \
                'Change to this directory before generating new files. It '
                'will make it if does not exists. default: "."'
        ),
    ]

    def __call__(self, args):
        template_path = path.join(TEMPLATES_PATH, args.template)
        target_path = path.abspath(args.directory)
        title_snakecase = args.name.lower()

        if not path.exists(template_path):
            print(f'Invalid template: {template_path}', file=sys.stderr)
            return 1

        if not path.exists(target_path):
            os.makedirs(target_path)

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
                if not args.overwrite and path.exists(target):
                    print(
                        f'Target file exists: {target}, use -o to overwrite',
                        file=sys.stderr
                    )
                    return 1

                os.makedirs(path.dirname(target), exist_ok=True)
                self.install_file(source, target, args)
                if args.template == 'singlefile':
                    os.chmod(target, 0o774)

    def install_file(self, source, target, args):
        print(f'Installing  {target}')
        title_snakecase = args.name.lower()
        title_camelcase = to_pascal_case(title_snakecase)

        with open(source) as s, open(target, 'w') as t:
            content = s.read()
            content = content.replace('${project_snakecase}', title_snakecase)
            content = content.replace('${project_author}', args.author)
            content = content.replace('${project_author_email}', args.email)
            content = content.replace('${project_camelcase}', title_camelcase)
            content = content.replace(
                '${restfulpy_version}',
                restfulpy.__version__
            )
            t.write(content)

