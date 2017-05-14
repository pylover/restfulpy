
import warnings

from nanohttp import Controller, context, settings, json, RestController, action

from restfulpy.orm import DBSession
from restfulpy.logging_ import get_logger
from restfulpy.authentication import Authenticator


warnings.filterwarnings('ignore', message='Unknown REQUEST_METHOD')


class RootController(Controller):
    __logger__ = get_logger()


class JwtController(RootController):
    __authenticator__ = Authenticator

    def begin_request(self):
        self.__authenticator__.authenticate_request()

    # noinspection PyMethodMayBeStatic
    def begin_response(self):
        if settings.debug:
            context.response_headers.add_header('Access-Control-Allow-Origin', 'http://localhost:8080')
            context.response_headers.add_header('Access-Control-Allow-Methods',
                                                'GET, POST, PUT, DELETE, UNDELETE, METADATA, PATCH, SEARCH')
            context.response_headers.add_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, '
                                                                                'X-HTTP-Verb')
            context.response_headers.add_header('Access-Control-Expose-Headers',
                                                'Content-Type, X-Pagination-Count, X-Pagination-Skip, '
                                                'X-Pagination-Take, X-New-JWT-Token')
            context.response_headers.add_header('Access-Control-Allow-Credentials', 'true')

    # noinspection PyMethodMayBeStatic
    def end_response(self):
        DBSession.remove()

    def __call__(self, *remaining_paths):
        if context.method == 'options':
            context.response_encoding = 'utf-8'
            context.response_headers.add_header("Cache-Control", "no-cache,no-store")
            return b''

        return super(JwtController, self).__call__(*remaining_paths)


class ModelRestController(RestController):
    __model__ = None

    @json
    def metadata(self):
        return self.__model__.json_metadata()


class JsonPatchControllerMixin:

    @action(content_type='application/json')
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
                context.form = patch.get('value', {})
                context.method = patch['op']

                return_data = self(*patch['path'].split('/'))
                results.append(return_data)

                DBSession.flush()
            DBSession.commit()
            return '[%s]' % ',\n'.join(results)
        except:
            if DBSession.is_active:
                DBSession.rollback()
            raise
        finally:
            del context.jsonpatch
