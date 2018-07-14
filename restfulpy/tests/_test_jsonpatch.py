import unittest

import ujson
from nanohttp import context, json, text, RestController, configure
from nanohttp.contexts import Context

from restfulpy.controllers import JsonPatchControllerMixin


class BiscuitsController(RestController):
    @json
    def put(self, id_: int = None):
        result = {}
        result.update(context.form)
        result['id'] = id_
        result['a'] = context.query.get('a')
        return result

    @json
    def get(self, id_: int = None):
        result = {}
        result.update(context.form)
        result['id'] = id_
        return result

    @json
    def error(self):
        raise Exception()


class SimpleJsonPatchController(JsonPatchControllerMixin, RestController):
    biscuits = BiscuitsController()

    @text
    def get(self):
        yield 'hey'


class JsonPatchTestCase(unittest.TestCase):
    __configuration__ = '''
    '''

    @classmethod
    def setUpClass(cls):
        configure(init_value=cls.__configuration__, force=True)

    def test_jsonpatch_rfc6902(self):
        environ = {
            'REQUEST_METHOD': 'PATCH'
        }
        with Context(environ):
            controller = SimpleJsonPatchController()
            context.form = [
                {"op": "get", "path": "/"},
                {"op": "put", "path": "biscuits/1", "value": {"name": "Ginger Nut"}},
                {"op": "get", "path": "biscuits/2", "value": {"name": "Ginger Nut"}},
            ]
            result = ujson.loads(controller())
            self.assertEqual(len(result), 3)

    def test_jsonpatch_error(self):
        environ = {
            'REQUEST_METHOD': 'PATCH'
        }
        with Context(environ):
            controller = SimpleJsonPatchController()
            context.form = [
                {"op": "put", "path": "biscuits/1", "value": {"name": "Ginger Nut"}},
                {"op": "error", "path": "biscuits", "value": None},
            ]
            self.assertRaises(Exception, controller)

    def test_jsonpatch_querystring(self):
        environ = {
            'REQUEST_METHOD': 'PATCH',
            'QUERY_STRING': 'a=10'
        }
        with Context(environ):
            controller = SimpleJsonPatchController()
            context.form = [
                {"op": "get", "path": "/"},
                {"op": "put", "path": "biscuits/1?a=1", "value": {"name": "Ginger Nut"}},
                {"op": "get", "path": "biscuits/2", "value": {"name": "Ginger Nut"}},
            ]
            result = ujson.loads(controller())
            self.assertEqual(len(result), 3)
            self.assertEqual(result[1]['a'], '1')
            self.assertNotIn('a', result[0])
            self.assertNotIn('a', result[2])

    def test_jsonpatch_caseinsesitive_verb(self):
        environ = {
            'REQUEST_METHOD': 'PATCH',
            'QUERY_STRING': 'a=10'
        }
        with Context(environ):
            controller = SimpleJsonPatchController()
            context.form = [
                {"op": "GET", "path": "/"},
                {"op": "PUT", "path": "biscuits/1?a=1", "value": {"name": "Ginger Nut"}},
                {"op": "GET", "path": "biscuits/2", "value": {"name": "Ginger Nut"}},
            ]
            result = ujson.loads(controller())
            self.assertEqual(len(result), 3)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
