import ujson

from restfulpy.cli import Launcher, RequireSubCommand
from restfulpy.principal import JwtPrincipal


class JWTLauncher(Launcher, RequireSubCommand):  # pragma: no cover
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser('jwt', help='JWT management')
        jwt_subparsers = parser.add_subparsers(
            title='JWT management',
            dest='jwt_command'
        )
        CreateJWTTokenLauncher.register(jwt_subparsers)
        return parser


class CreateJWTTokenLauncher(Launcher):  # pragma: no cover
    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser(
            'create',
            help='Create a new initial jwt.'
        )
        parser.add_argument(
            '-e', '--expire-in',
            default=3600,
            type=int,
            help='the max age, default: 3600 (one hour).'
        )
        parser.add_argument(
            'payload',
            default='{}',
            nargs='?',
            help= \
                'A JSON parsable string to treat as payload. for example: '
                '{"a": "b"}'
        )
        return parser

    def launch(self):
        payload = ujson.loads(self.args.payload)
        print(JwtPrincipal(payload).dump(self.args.expire_in).decode())

