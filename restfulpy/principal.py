import base64

from itsdangerous import TimedJSONWebSignatureSerializer, JSONWebSignatureSerializer
from nanohttp import settings, context

from restfulpy.utils import deprecated


class JwtPrincipal:
    def __init__(self, payload):
        self.payload = payload

    @classmethod
    def create_serializer(cls, force=False):
        if force:
            return JSONWebSignatureSerializer(
                settings.jwt.secret,
                algorithm_name=settings.jwt.algorithm
            )
        else:
            return TimedJSONWebSignatureSerializer(
                settings.jwt.secret,
                expires_in=settings.jwt.max_age,
                algorithm_name=settings.jwt.algorithm
            )

    @deprecated
    def encode(self):
        """Use ``dump`` instead.
        """
        return self.dump()

    def dump(self):
        return self.create_serializer().dumps(self.payload)

    @classmethod
    @deprecated
    def decode(cls, encoded, force=False):
        """Use ``load`` instead.
        """
        return cls.load(encoded, force=force)

    @classmethod
    def load(cls, encoded, force=False):
        if encoded.startswith('Bearer '):
            encoded = encoded[7:]
        if encoded.startswith('Basic '):
            encoded = base64.decodebytes(encoded[6:].encode())
        payload = cls.create_serializer(force=force).loads(encoded)
        return cls(payload)

    def is_in_roles(self, *roles):
        if 'roles' in self.payload:
            if set(self.payload['roles']).intersection(roles):
                return True
        return False

    @property
    def email(self):
        return self.payload.get('email')

    @property
    def session_id(self):
        return self.payload.get('sessionId')

    @property
    def id(self):
        return self.payload.get('id')

    @property
    def roles(self):
        return self.payload.get('roles', [])


class JwtRefreshToken:
    def __init__(self, payload):
        self.payload = payload

    @classmethod
    def create_serializer(cls):
        return TimedJSONWebSignatureSerializer(
            settings.jwt.refresh_token.secret,
            expires_in=settings.jwt.refresh_token.max_age,
            algorithm_name=settings.jwt.refresh_token.algorithm
        )

    def dump(self):
        return self.create_serializer().dumps(self.payload)

    @classmethod
    def load(cls, encoded):
        payload = cls.create_serializer().loads(encoded)
        return cls(payload)

    @property
    def id(self):
        return self.payload.get('id')


class DummyIdentity(JwtPrincipal):
    def __init__(self, *roles):
        super().__init__({'roles': list(roles)})


class ImpersonateAs:
    backup_identity = None

    def __init__(self, principal):
        self.principal = principal

    def __enter__(self):
        if hasattr(context, 'identity'):
            self.backup_identity = context.identity
        context.identity = self.principal

    def __exit__(self, exc_type, exc_val, exc_tb):
        context.identity = self.backup_identity
