

import itsdangerous

from nanohttp import context, HttpBadRequest, HttpCookie, settings

from restfulpy.principal import JwtPrincipal, JwtRefreshToken


class Authenticator:
    """
    An extendable abstract static class for encapsulating all stuff about authentication
    """

    token_key = 'HTTP_AUTHORIZATION'
    refresh_token_cookie_key = 'refresh-token'
    token_response_header = 'X-New-JWT-Token'

    def create_principal(self, member_id=None, session_id=None):
        raise NotImplementedError()

    def create_refresh_principal(self, member_id=None):
        raise NotImplementedError()

    def validate_credentials(self, credentials):
        raise NotImplementedError()

    def setup_response_headers(self, new_principal):
        context.response_headers.add_header(self.token_response_header, new_principal.dump().decode())

    def try_refresh_token(self, session_id):
        refresh_token_encoded = context.cookies.get(self.refresh_token_cookie_key)

        if refresh_token_encoded is None or not refresh_token_encoded.strip():
            self.bad()
            return

        # Decode refresh token
        try:
            refresh_principal = JwtRefreshToken.load(refresh_token_encoded)
            self.ok(
                self.create_principal(member_id=refresh_principal.id, session_id=session_id),
                setup_header=True
            )
        except itsdangerous.SignatureExpired:
            self.bad()
        except itsdangerous.BadData:
            self.bad()
            raise HttpBadRequest()

    def bad(self):
        context.identity = None

    def ok(self, principal, setup_header=False):
        context.identity = principal
        if setup_header:
            self.setup_response_headers(principal)

    def authenticate_request(self):
        if self.token_key not in context.environ:
            self.bad()
            return

        encoded_token = context.environ[self.token_key]
        if encoded_token is None or not encoded_token.strip():
            self.bad()
            return

        try:
            self.ok(JwtPrincipal.load(encoded_token))

        except itsdangerous.SignatureExpired as ex:
            # The token has expired. So we're trying to restore it using refresh-token.
            session_id = ex.payload.get('sessionId')
            if session_id:
                self.try_refresh_token(session_id)
        except itsdangerous.BadData:
            # The token is Malformed
            self.bad()
            raise HttpBadRequest()

    def login(self, credentials):
        member = self.validate_credentials(credentials)
        if member is None:
            return None

        principal = self.create_principal(member.id)
        
        context.response_cookies.append(HttpCookie(
            'refresh-token',
            value=self.create_refresh_principal(member.id).dump().decode(),
            max_age=settings.jwt.refresh_token.max_age,
            http_only=False,
            secure=True
        ))

        return principal
