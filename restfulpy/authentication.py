
import itsdangerous
import redis
from nanohttp import context, HttpBadRequest, settings

from restfulpy.principal import JwtPrincipal, JwtRefreshToken


class Authenticator:
    """
    An extendable stateless abstract class for encapsulating all stuff about authentication
    """

    token_key = 'HTTP_AUTHORIZATION'
    refresh_token_key = 'refresh-token'
    token_response_header = 'X-New-JWT-Token'
    identity_response_header = 'X-Identity'

    def create_principal(self, member_id=None, session_id=None):
        raise NotImplementedError()

    def create_refresh_principal(self, member_id=None):
        raise NotImplementedError()

    def validate_credentials(self, credentials):
        raise NotImplementedError()

    def setup_response_headers(self, new_principal):
        if self.token_response_header in context.response_headers:
            del context.response_headers[self.token_response_header]
        context.response_headers.add_header(self.token_response_header, new_principal.dump().decode())

    def try_refresh_token(self, session_id):
        morsel = context.cookies.get(self.refresh_token_key)
        if not morsel:
            self.bad()
            return

        refresh_token_encoded = morsel.value
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

    def setup_identity_response_header(self, principal):
        context.response_headers.add_header(self.identity_response_header, str(principal.id) if principal else '')

    def bad(self):
        context.identity = None
        self.setup_identity_response_header(None)

    def ok(self, principal, setup_header=False):
        context.identity = principal
        self.setup_identity_response_header(principal)
        if setup_header:
            self.setup_response_headers(principal)

    def verify_token(self, encoded_token):
        return JwtPrincipal.load(encoded_token)

    def authenticate_request(self):
        if self.token_key not in context.environ:
            self.bad()
            return

        encoded_token = context.environ[self.token_key]
        if encoded_token is None or not encoded_token.strip():
            self.bad()
            return

        try:
            self.ok(self.verify_token(encoded_token))

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

        self.ok(principal)

        context.cookies[self.refresh_token_key] = self.create_refresh_principal(member.id).dump().decode()
        context.cookies[self.refresh_token_key]['max-age'] = settings.jwt.refresh_token.max_age
        context.cookies[self.refresh_token_key]['httponly'] = False
        context.cookies[self.refresh_token_key]['secure'] = True
        return principal

    def logout(self):
        self.bad()


# noinspection PyAbstractClass
class StatefulAuthenticator(Authenticator):
    """
    
    Redis data-model:
    
    sessions: HashMap { session_id: member_id }
    member_id: Set { session_id } 
    
    
    """

    _redis = None
    sessions_key = 'auth:sessions'
    members_key = 'auth:member:%s'

    def __init__(self):
        super().__init__()

    @staticmethod
    def create_blocking_redis_client():
        # FIXME: use unix socket
        return redis.StrictRedis(
            host=settings.authentication.redis.host,
            port=settings.authentication.redis.port,
            db=settings.authentication.redis.db,
            password=settings.authentication.redis.password
        )

    @property
    def redis(self):
        if self.__class__._redis is None:
            self.__class__._redis = self.create_blocking_redis_client()
        return self.__class__._redis

    @classmethod
    def get_session_key(cls, session_id):
        return 'auth:session:%s' % session_id

    @classmethod
    def get_member_sessions_key(cls, member_id):
        return 'auth:member:%s' % member_id

    def verify_token(self, encoded_token):
        principal = super().verify_token(encoded_token)
        if not self.validate_session(principal.session_id):
            raise itsdangerous.SignatureExpired('The token has already invalidated', principal.payload)
        return principal

    def login(self, credentials):
        principal = super().login(credentials)
        if principal is not None:
            self.register_session(principal.id, principal.session_id)
        return principal

    def logout(self):
        self.unregister_session(context.identity.session_id)
        super().logout()

    def register_session(self, member_id, session_id):
        self.redis.hset(self.sessions_key, session_id, member_id)
        self.redis.sadd(self.get_member_sessions_key(member_id), session_id)

    def unregister_session(self, session_id=None):
        session_id = session_id or context.identity.session_id
        member_id = self.redis.hget(self.sessions_key, session_id)
        self.redis.srem(self.get_member_sessions_key(member_id), session_id)
        self.redis.hdel(self.sessions_key, session_id)

    def invalidate_member(self, member_id=None):
        # store current session id if available
        current_session_id = None if context.identity is None else context.identity.session_id
        while True:
            session_id = self.redis.spop(self.get_member_sessions_key(member_id))
            if not session_id:
                break
            self.redis.hdel(self.sessions_key, session_id)
        self.redis.delete(self.get_member_sessions_key(member_id))
        if current_session_id:
            self.try_refresh_token(current_session_id)

    def validate_session(self, session_id):
        return self.redis.hexists(self.sessions_key, session_id)
