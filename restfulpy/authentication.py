

import itsdangerous

from nanohttp import context, HttpBadRequest

from restfulpy.principal import JwtPrincipal, JwtRefreshToken


class Authenticator:
    """
    An extendable abstract static class for encapsulating all stuff about authentication
    """

    token_key = 'HTTP_AUTHORIZATION'
    refresh_token_cookie_key = 'refresh-token'
    token_response_header = 'X-New-JWT-Token'

    @classmethod
    def create_principal(cls, refresh_principal=None, session_id=None):
        raise NotImplementedError()

    @classmethod
    def setup_response_headers(cls, new_principal):
        context.response_headers.add_header(cls.token_response_header, new_principal.dump().decode())

    @classmethod
    def try_refresh_token(cls, session_id):
        refresh_token_encoded = context.cookies.get(cls.refresh_token_cookie_key)

        if refresh_token_encoded is None or not refresh_token_encoded.strip():
            cls.bad()
            return

        # Decode refresh token
        try:
            refresh_principal = JwtRefreshToken.load(refresh_token_encoded)
            cls.ok(
                cls.create_principal(refresh_principal=refresh_principal, session_id=session_id),
                setup_header=True
            )
        except itsdangerous.SignatureExpired:
            cls.bad()
        except itsdangerous.BadData:
            cls.bad()
            raise HttpBadRequest()

    @classmethod
    def bad(cls):
        context.identity = None

    @classmethod
    def ok(cls, principal, setup_header=False):
        context.identity = principal
        if setup_header:
            cls.setup_response_headers(principal)

    @classmethod
    def authenticate_request(cls):
        if cls.token_key not in context.environ:
            cls.bad()
            return

        encoded_token = context.environ[cls.token_key]
        if encoded_token is None or not encoded_token.strip():
            cls.bad()
            return

        try:
            cls.ok(JwtPrincipal.load(encoded_token))

        except itsdangerous.SignatureExpired as ex:
            # The token has expired. So we're trying to restore it using refresh-token.
            session_id = ex.payload.get('sessionId')
            if session_id:
                cls.try_refresh_token(session_id)
        except itsdangerous.BadData:
            # The token is Malformed
            cls.bad()
            raise HttpBadRequest()
