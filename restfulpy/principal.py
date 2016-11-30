
# noinspection PyPackageRequirements
import jwt

from nanohttp import settings


class JwtPrincipal:

    def __init__(self, payload):
        self.payload = payload

    def encode(self):
        return jwt.encode(self.payload, settings.jwt.secret, algorithm=settings.jwt.algorithm)

    @classmethod
    def decode(cls, encoded):
        payload = jwt.decode(encoded, settings.jwt.secret, algorithms=[settings.jwt.algorithm])
        return cls(payload)

    def is_in_roles(self, *roles):
        if 'roles' in self.payload:
            if set(self.payload['roles']).intersection(roles):
                return True
        return False

    @property
    def email(self):
        return self.payload.get('email')
