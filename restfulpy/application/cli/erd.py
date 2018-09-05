import sys
from os import makedirs, path
from os.path import join

from nanohttp import settings
from sqlalchemy import MetaData

from restfulpy.cli import Launcher


class EntityRelationshipDiagrams(Launcher):
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser(
            'entity-relationship-diagram',
            help='Generate erd from database. '
                 'Make sure database and tables exists.'
        )

        parser.add_argument(
            '-u',
            '--url',
            type=str,
            default=None,
            help='DB url.'
        )

        parser.add_argument(
            '-o',
            '--output',
            type=str,
            default='data/class-diagrams/schema.png',
            help='Output file name.'
        )

        parser.add_argument(
            '-d',
            '--datatype',
            type=bool,
            default=True,
            help='Show datatypes.'
        )

        parser.add_argument(
            '-i',
            '--index',
            type=bool,
            default=True,
            help='Show indexes.'
        )

        parser.add_argument(
            '-c',
            '--concentrate',
            type=bool,
            default=True,
            help='Concentrate.'
        )

        parser.add_argument(
            '-r',
            '--rankdir',
            type=str,
            default='LR',
            help='Rankdir.'
        )

        return parser

    def launch(self):
        try:
            from sqlalchemy_schemadisplay import create_schema_graph
        except ImportError:
            print(
                'You have to install sqlalchemy_schemadisplay to use this '
                'feature',
                file=sys.stderr
            )
            sys.exit(1)

        db_url = self.args.url if self.args.url else settings.db.url
        try:
            metadata = MetaData(db_url)
            graph = create_schema_graph(
                metadata=metadata,
                show_datatypes=self.args.datatype,
                show_indexes=self.args.index,
                rankdir=self.args.rankdir,
                concentrate=self.args.concentrate)

        except Exception as ex:
            print(ex)
            return

        output_dir = \
            join(self.args.application.root_path, 'data/class-diagrams/')
        output = join(output_dir, self.args.output)
        makedirs(path.dirname(output), exist_ok=True)

        try:
            graph.write_png(output)
            print('ERD generated in', output)
            print('If it is empty, probably you need to create schema of db.')
        except FileNotFoundError:
            print("You need to install graphviz, see this link: \n"
                  "https://www.graphviz.org/download/")
        except Exception as ex:
            print(ex)

