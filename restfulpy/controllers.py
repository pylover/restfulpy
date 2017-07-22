
from nanohttp import Controller, context, json, RestController, action, etag

from restfulpy.orm import DBSession


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
    @etag(tag=lambda: context.application.version)
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

                remaining_paths = patch['path'].split('/')
                if remaining_paths and not remaining_paths[0]:
                    return_data = self()
                else:
                    return_data = self(*remaining_paths)

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
