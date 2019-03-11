from easycli import Root, Argument

from .scaffolding.launchers import ScaffoldSubCommand


class Restfulpy(Root):
    __help__ = 'Restfylpy command line interface'
    __completion__ = True
    __arguments__ = [
        Argument(
            '-V',
            '--version',
            action='store_true',
            help='Show version'
        ),
        ScaffoldSubCommand,
    ]

    def __call__(self, args):
        if args.version:
            from restfulpy import __version__
            print(__version__)
            return

        return super().__call__(args)


def Main():
    return Restfulpy().main()

