
from restfulpy.principal import JwtPrincipal

from nanohttp import Controller, context, settings


class JwtController(Controller):
    token_key = 'HTTP_X_JWT_TOKEN'

    def begin_request(self):
        if self.token_key in context.environ:
            context.identity = JwtPrincipal.decode(context.environ[self.token_key])
        else:
            context.identity = None

    # noinspection PyMethodMayBeStatic
    def begin_response(self):
        if settings.debug:
            context.response_headers.add_header('Access-Control-Allow-Origin', '*')
            context.response_headers.add_header('Access-Control-Allow-Headers', 'Content-Type, X-JWT-Token')

    def __call__(self, *remaining_paths):
        if context.method == 'options':
            return ''

        return super(JwtController, self).__call__(*remaining_paths)
