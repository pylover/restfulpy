import re
from datetime import datetime

import itsdangerous
import redis
import ujson
import user_agents
from nanohttp import context, HTTPBadRequest, settings, HTTPUnauthorized

from restfulpy.principal import JwtPrincipal, JwtRefreshToken


class Authenticator:
    """
    An extendable stateless abstract class for encapsulating all stuff about
    authentication
                                                            +
                                                            |
                                              Yes  +--------+-------+  No
                                              +----+  Token Exists? +-----+
                                              |    +----------------+     |
                                              |                           |
                                              |                           |
                                              |                           |
                                 No  +--------+-------+  Yes              |
                                +----+ Verify Tokens? +------+            |
                                |    +----------------+      |            |
                                |                            |    Continue|
        +---+         Yes +-----+-----+                      |       as   |
        |400+^------------+  Damaged? |                      |     isitor |
        +---+             +-----------+                      |            |
                              No|                            |            |
                                |                            |            |
                           +----+----+                       |            |
                           | Expired |                       |            |
                           +----+----+                       |            |
                                |                            |            |
                           +----+----+                       |            |
        +---+         No   | Refresh |                       |            |
        |401+^-------------+ Token   |                 As Use|            |
        +---+              | Exists? |                       |            |
                           +----+----+                       |            |
                                |                            |            |
                             Yes|                            |            |
                                |                            |            |
        +---+       No +--------+---------+                  |            |
        |400+^---------+Is connection SSL?|                  |            |
        +---+          +--------+---------+                  |            |
                                |                            |            |
                            Yes |                            |            |
                                |                            |            |
                       +--------+---------+                  |            |
                       |                  |                  |            |
                       |                  |                  |            |
                       |   Renew Token    |                  |            |
                       |        &         |                  |            |
                       |   Add to Header  |                  |            |
                       |                  |                  |            |
                       |                  |                  |            |
                       +--------+---------+                  |            |
                                |                            |            |
                                |                            |            |
                                |                            |            |
                                |                            |            |
                                |                            |            |
                                |          +----------+      |            |
                                +----------> WSGI App <------+------------+
                                           +----------+



    """

    token_key = 'HTTP_AUTHORIZATION'
    refresh_token_key = 'refresh-token'
    token_response_header = 'X-New-JWT-Token'
    identity_response_header = 'X-Identity'

    def create_principal(self, member_id=None, session_id=None, **kwargs):  # pragma: no cover
        raise NotImplementedError()

    def create_refresh_principal(self, member_id=None):  # pragma: no cover
        raise NotImplementedError()

    def validate_credentials(self, credentials):  # pragma: no cover
        raise NotImplementedError()

    def setup_response_headers(self, new_principal):
        if self.token_response_header in context.response_headers:
            del context.response_headers[self.token_response_header]
        context.response_headers.add_header(
            self.token_response_header,
            new_principal.dump().decode()
        )

    def try_refresh_token(self, session_id):
        morsel = context.cookies.get(self.refresh_token_key)
        if not morsel:
            return self.bad()

        if settings.jwt.refresh_token.secure \
                and context.request_scheme != 'https':
            raise HTTPBadRequest('not allowed')

        if morsel.value is None or not morsel.value.strip():
            return self.bad()

        refresh_token_encoded = morsel.value
        # Decoding the refresh token
        try:
            refresh_principal = JwtRefreshToken.load(refresh_token_encoded)
            self.ok(
                self.create_principal(
                    member_id=refresh_principal.id,
                    session_id=session_id
                ),
                setup_header=True
            )
        except itsdangerous.SignatureExpired:
            self.bad()
        except itsdangerous.BadData:
            self.bad()
            raise HTTPBadRequest()

    def setup_identity_response_header(self, principal):
        if self.identity_response_header in context.response_headers:
            del context.response_headers[self.identity_response_header]

        if principal is not None:
            context.response_headers.add_header(
                self.identity_response_header,
                str(principal.id)
            )

        if principal is None and self.refresh_token_key in context.cookies:
            del context.cookies[self.refresh_token_key]

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
            # The token has expired. So we're trying to restore it using
            # refresh-token.
            session_id = ex.payload.get('sessionId')
            if session_id:
                self.try_refresh_token(session_id)
            else:
                self.bad()
                raise HTTPUnauthorized()
        except itsdangerous.BadData:
            # The token is Malformed
            self.bad()
            raise HTTPBadRequest()

    def login(self, credentials):
        member = self.validate_credentials(credentials)
        if member is None:
            return None

        principal = self.create_principal(member.id)

        self.ok(principal)

        context.cookies[self.refresh_token_key] = \
            self.create_refresh_principal(member.id).dump().decode()
        context.cookies[self.refresh_token_key]['max-age'] = \
            settings.jwt.refresh_token.max_age
        context.cookies[self.refresh_token_key]['httponly'] = \
            settings.jwt.refresh_token.httponly
        context.cookies[self.refresh_token_key]['secure'] = \
            settings.jwt.refresh_token.secure
        if 'path' in settings.jwt.refresh_token:
            context.cookies[self.refresh_token_key]['path'] = \
                settings.jwt.refresh_token.path

        return principal

    def logout(self):
        self.bad()


class StatefulAuthenticator(Authenticator):
    """

    Redis data-model:

        sessions: HashMap { session_id: member_id }
        member:{member_id}: Set { session_id }
        sessions:{session_id}:info:  String { user-agent }

    User-Agent structure: {
        remoteAddress: 127.0.0.1,
        machine: pc,
        os: android 4.2.2,
        agent: chrome 55,
        client: RestfulpyClient-js 3.4.5-alpha14,
        app: Mobile Token (shark) 1.5.4,
        lastActivity: 2015-10-26T07:46:36.615661
    }

        User-Agent can contains customized token and comment in order to
        describe client and app.

        User-Agent: TOKEN (COMMENT)

        TOKEN: RestfulpyClient-TYPE/VERSION
            exp: RestfulpyClient-js/1.2.3

        COMMENT: (APP-TITLE; APP-NAME; APP-VERSION; APP-LOCALIZATION
                 [; OPTIONAL-OTHER-COMMENTS]*)
            exp: (Mobile Token; shark; 1.2.3-preview2; en-US)

        Tips:
            1. TOKEN must not contain any of CLRs or separators
            2. COMMENTS: any TEXT excluding "(" and ")" and ";"
            3. If you don't use one of standard clients of restfulpy, you can
               use this format as TOKEN: RestfulpyClient-custom/0.0.0

    """

    _redis = None
    sessions_key = 'auth:sessions'
    members_key = 'auth:member:%s'
    session_info_key = 'auth:sessions:%s:info'
    remote_address_key = 'REMOTE_ADDR'
    agent_key = 'HTTP_USER_AGENT'

    @staticmethod
    def create_blocking_redis_client():
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
    def get_member_sessions_key(cls, member_id):
        return cls.members_key % member_id

    @classmethod
    def get_session_info_key(cls, session_id):
        return cls.session_info_key % session_id

    def verify_token(self, encoded_token):
        principal = super().verify_token(encoded_token)
        if not self.validate_session(principal.session_id):
            raise itsdangerous.SignatureExpired(
                'The token has already invalidated',
                principal.payload
            )
        return principal

    def login(self, credentials):
        principal = super().login(credentials)
        if principal is not None:
            self.register_session(principal.id, principal.session_id)
        return principal

    def logout(self):
        self.unregister_session(context.identity.session_id)
        super().logout()

    def extract_agent_info(self):
        remote_address = None
        machine = None
        os = None
        agent = None

        if self.remote_address_key in context.environ \
                and context.environ[self.remote_address_key]:
            remote_address = context.environ[self.remote_address_key]

        if self.agent_key in context.environ:
            agent_string = context.environ[self.agent_key]
            user_agent = user_agents.parse(agent_string)

            machine = user_agent.is_pc and 'PC' or user_agent.device.family
            os = ' '.join([
                user_agent.os.family,
                user_agent.os.version_string
            ]).strip()
            agent = ' '.join([
                user_agent.browser.family,
                user_agent.browser.version_string
            ]).strip()

        return {
            'remoteAddress': remote_address or 'NA',
            'machine': machine or 'Other',
            'os': os or 'Other',
            'agent': agent or 'Other',
            'lastActivity': datetime.utcnow().isoformat()
        }

    def register_session(self, member_id, session_id):
        self.redis.hset(self.sessions_key, session_id, member_id)
        self.redis.sadd(self.get_member_sessions_key(member_id), session_id)
        self.redis.set(
            self.get_session_info_key(session_id),
            ujson.dumps(self.extract_agent_info())
        )

    def unregister_session(self, session_id=None):
        session_id = session_id or context.identity.session_id
        member_id = self.redis.hget(self.sessions_key, session_id)
        self.redis.srem(self.get_member_sessions_key(member_id), session_id)
        self.redis.hdel(self.sessions_key, session_id)
        self.redis.delete(self.get_session_info_key(session_id))

    def invalidate_member(self, member_id=None):
        # store current session id if available
        current_session_id = \
            None if context.identity is None else context.identity.session_id
        while True:
            session_id = self.redis.spop(
                self.get_member_sessions_key(member_id)
            )
            if not session_id:
                break
            self.redis.hdel(self.sessions_key, session_id)
            self.redis.delete(self.get_session_info_key(session_id))
        self.redis.delete(self.get_member_sessions_key(member_id))
        if current_session_id:
            self.try_refresh_token(current_session_id)

    def validate_session(self, session_id):
        return self.redis.hexists(self.sessions_key, session_id)

    def get_member_id_by_session(self, session_id):
        return int(self.redis.hget(self.sessions_key, session_id))

    def ok(self, principal, setup_header=False):
        super().ok(principal, setup_header)
        self.update_session_info(principal.session_id)

    def update_session_info(self, session_id):
        self.redis.set(
            self.get_session_info_key(session_id),
            ujson.dumps(self.extract_agent_info())
        )

    def get_session_info(self, session_id):
        info = self.redis.get(self.get_session_info_key(session_id))
        if info:
            return ujson.loads(info)
        return None

