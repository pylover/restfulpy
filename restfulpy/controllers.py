
import warnings
import itsdangerous

from nanohttp import Controller, context, settings, json, RestController

from restfulpy.principal import JwtPrincipal
from restfulpy.orm import DBSession


warnings.filterwarnings('ignore', message='Unknown REQUEST_METHOD')


class JwtController(Controller):
    token_key = 'HTTP_AUTHORIZATION'
    refresh_token_cookie_key = 'refresh-token'

    def begin_request(self):
        if self.token_key in context.environ:
            encoded_token = context.environ[self.token_key]
            try:
                context.identity = JwtPrincipal.decode(encoded_token)
            except itsdangerous.SignatureExpired as ex:
                refresh_token_encoded = context.cookies.get(self.refresh_token_cookie_key)
                if refresh_token_encoded:
                    # Extracting session_id
                    session_id = ex.payload.get('sessionId')
                    if session_id:
                        context.identity = new_token = self.refresh_jwt_token(refresh_token_encoded, session_id)
                        if new_token:
                            context.response_headers.add_header('X-New-JWT-Token', new_token.encode().decode())

            except itsdangerous.BadData:
                pass

        if not hasattr(context, 'identity'):
            context.identity = None

    def refresh_jwt_token(self, refresh_token_encoded, session_id):
        raise NotImplementedError

    # noinspection PyMethodMayBeStatic
    def begin_response(self):
        if settings.debug:
            context.response_headers.add_header('Access-Control-Allow-Origin', 'http://localhost:8080')
            context.response_headers.add_header('Access-Control-Allow-Methods',
                                                'GET, POST, PUT, DELETE, UNDELETE, METADATA, PATCH')
            context.response_headers.add_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            context.response_headers.add_header('Access-Control-Expose-Headers',
                                                'Content-Type, X-Pagination-Count, X-Pagination-Skip, '
                                                'X-Pagination-Take, X-New-JWT-Token')
            context.response_headers.add_header('Access-Control-Allow-Credentials', 'true')

    # noinspection PyMethodMayBeStatic
    def end_response(self):
        DBSession.remove()

    def __call__(self, *remaining_paths):
        if context.method == 'options':
            context.response_headers.add_header("Cache-Control", "no-cache,no-store")
            return b''

        return super(JwtController, self).__call__(*remaining_paths)


class ModelRestController(RestController):
    __model__ = None

    @json
    def metadata(self):
        return self.__model__.json_metadata()


class JsonPatchControllerMixin:

    @json
    def patch(self: Controller):
        """
        Set context.method
        Set context.form
        :return:
        """
        # Preserve patches
        patches = context.form
        results = []
        context.jsonpatch = True

        try:
            for patch in patches:
                context.form = patch['value']
                context.method = patch['op']
                results.append(self(*patch['path'].split('/')))
                DBSession.flush()
            DBSession.commit()
            return results
        except:
            if DBSession.is_active:
                DBSession.rollback()
            raise
        finally:
            del context.jsonpatch
