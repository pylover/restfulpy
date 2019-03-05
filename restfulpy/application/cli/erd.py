import sys
from os import makedirs, path
from os.path import join

from easycli import SubCommand, Argument
from nanohttp import settings
from sqlalchemy import MetaData


class EntityRelationshipDiagramsSubCommand(SubCommand):
    __command__ = 'entity-relationship-diagram'
    __help__ = 'Generate erd from database. Make sure database and ' \
        'tables exists.'
    __arguments__ = [
        Argument(
            '-u',
            '--url',
            type=str,
            default=None,
            help='DB url.',
        ),
        Argument(
            '-o',
            '--output',
            type=str,
            default='data/class-diagrams/schema.png',
            help='Output file name.',
        ),
        Argument(
            '-d',
            '--datatype',
            type=bool,
            default=True,
            help='Show datatypes.',
        ),
        Argument(
            '-i',
            '--index',
            type=bool,
            default=True,
            help='Show indexes.',
        ),
        Argument(
            '-c',
            '--concentrate',
            type=bool,
            default=True,
            help='Concentrate.',
        ),
        Argument(
            '-r',
            '--rankdir',
            type=str,
            default='LR',
            help='Rankdir.',
        ),
    ]

    def __call__(self, args):
        try:
            from sqlalchemy_schemadisplay import create_schema_graph

        except ImportError:
            print(
                'You have to install sqlalchemy_schemadisplay to use this '
                'feature',
                file=sys.stderr
            )
            sys.exit(1)

        db_url = args.url if args.url else settings.db.url
        try:
            metadata = MetaData(db_url)
            graph = create_schema_graph(
                metadata=metadata,
                show_datatypes=args.datatype,
                show_indexes=args.index,
                rankdir=args.rankdir,
                concentrate=args.concentrate,
            )

        except Exception as ex:
            print(ex)
            return

        output_dir = join(args.application.root_path, 'data/class-diagrams/')
        output = join(output_dir, args.output)
        makedirs(path.dirname(output), exist_ok=True)

        try:
            graph.write_png(output)
            print('ERD generated in', output)
            print('If it is empty, probably you need to create schema of db.')

        except FileNotFoundError:
            print(
                'You need to install graphviz, see this link: \n'
                'https://www.graphviz.org/download/'
            )

        except Exception as ex:
            print(ex)

