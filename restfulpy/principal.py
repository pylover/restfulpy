from itsdangerous import TimedJSONWebSignatureSerializer, \
    JSONWebSignatureSerializer
from nanohttp import settings, context, HTTPForbidden


class BaseJwtPrincipal:
    def __init__(self, payload):
        self.payload = payload

    @classmethod
    def create_serializer(cls, force=False, max_age=None):
        config = cls.get_config()

        if force:
            return JSONWebSignatureSerializer(
                config['secret'],
                algorithm_name=config['algorithm']
            )
        else:
            return TimedJSONWebSignatureSerializer(
                config['secret'],
                expires_in=max_age or config['max_age'],
                algorithm_name=config['algorithm']
            )

    def dump(self, max_age=None):
        return self.create_serializer(max_age=max_age).dumps(self.payload)

    @classmethod
    def load(cls, encoded, force=False):
        if encoded.startswith('Bearer '):
            encoded = encoded[7:]
        payload = cls.create_serializer(force=force).loads(encoded)
        return cls(payload)

    @classmethod
    def get_config(cls):
        raise NotImplementedError()


class JwtPrincipal(BaseJwtPrincipal):
    def is_in_roles(self, *roles):
        if 'roles' in self.payload:
            if set(self.payload['roles']).intersection(roles):
                return True
        return False

    def assert_roles(self, *roles):
        """
        .. versionadded:: 0.29

        :param roles:
        :return:
        """
        if roles and not self.is_in_roles(*roles):
            raise HTTPForbidden()

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

    @classmethod
    def get_config(cls):
        """
        Warning! Returned value is a dict, so it's mutable. If you modify this
        value, default config of the whole project will be changed and it may
        cause unpredictable problems.
        """
        return settings.jwt


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
