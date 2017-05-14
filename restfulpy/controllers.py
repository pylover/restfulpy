
import warnings

from nanohttp import Controller, context, json, RestController, action

from restfulpy.orm import DBSession


warnings.filterwarnings('ignore', message='Unknown REQUEST_METHOD')


class RootController(Controller):

    def __call__(self, *remaining_paths):

        if context.method == 'options':
            context.response_encoding = 'utf-8'
            context.response_headers.add_header("Cache-Control", "no-cache,no-store")
            return b''

        return super().__call__(*remaining_paths)


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
