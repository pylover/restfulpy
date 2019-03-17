import ujson
from easycli import SubCommand, Argument

from restfulpy.principal import JwtPrincipal


class CreateJWTTokenSubSubCommand(SubCommand):
    __command__ = 'create'
    __help__ = 'Create a new initial jwt'
    __arguments__ = [
        Argument(
            '-e',
            '--expire-in',
            default=3600,
            type=int,
            help='the max age, default: 3600 (one hour).',
        ),
        Argument(
            'payload',
            default='{}',
            nargs='?',
            help='A JSON parsable string to treat as payload. for example: ' \
                '{"a": "b"}',
        ),
    ]

    def __call__(self, args):
        payload = ujson.loads(args.payload)
        print(JwtPrincipal(payload).dump(args.expire_in).decode())


class JWTSubCommand(SubCommand):
    __command__ = 'jwt'
    __help__ = 'JWT management'
    __arguments__ = [
        CreateJWTTokenSubSubCommand,
    ]

