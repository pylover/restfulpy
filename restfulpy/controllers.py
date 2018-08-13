import types
from urllib.parse import parse_qs

from nanohttp import Controller, context, json, RestController, action

from restfulpy.orm import DBSession


class RootController(Controller):

    def __call__(self, *remaining_paths):

        if context.method == 'options':
            context.response_encoding = 'utf-8'
            context.response_headers.add_header(
                'Cache-Control',
                'no-cache,no-store'
            )
            return b''

        return super().__call__(*remaining_paths)


class ModelRestController(RestController):
    __model__ = None

    @json
    def metadata(self):
        return self.__model__.json_metadata()


def split_path(url):
    if '?' in url:
        path, query = url.split('?')
    else:
        path, query = url, ''

    return path, {k: v[0] if len(v) == 1 else v for k, v in parse_qs(
        query,
        keep_blank_values=True,
        strict_parsing=False
    ).items()}


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
                path, context.query = split_path(patch['path'])
                context.method = patch['op'].lower()

                remaining_paths = path.split('/')
                if remaining_paths and not remaining_paths[0]:
                    return_data = self()
                else:
                    return_data = self(*remaining_paths)

                if isinstance(return_data, types.GeneratorType):
                    results.append('"%s"' % ''.join(list(return_data)))
                else:
                    results.append(return_data)

                DBSession.flush()
                context.query = {}

            DBSession.commit()
            return '[%s]' % ',\n'.join(results)
        except:
            if DBSession.is_active:
                DBSession.rollback()
            raise
        finally:
            del context.jsonpatch
