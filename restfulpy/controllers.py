
from restfulpy.principal import JwtPrincipal

from nanohttp import Controller, context


class JwtController(Controller):
    token_key = 'HTTP_X_JWT_TOKEN'

    def begin_request(self):
        if self.token_key in context.environ:
            context.identity = JwtPrincipal.decode(context.environ[self.token_key])
        else:
            context.identity = None



