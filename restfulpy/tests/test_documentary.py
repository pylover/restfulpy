
import unittest

from nanohttp import Controller, text, context, json

from restfulpy.documentary import AbstractDocumentaryMiddleware, WSGIDocumentaryTestCase, Response, \
    FileDocumentaryMiddleware


last_call = None


class ExaminationMiddleware(AbstractDocumentaryMiddleware):
    def on_call_done(self, call):
        global last_call
        last_call = call


class Root(Controller):
    @text
    def index(self, id_='empty'):
        yield f'Content {id_}'

    @text
    def books(self, isbn, name=None):
        yield f'Book {isbn}'
        if name:
            yield f' {name}'

    @text
    def search(self, resource, *, query=None):
        yield f'{resource} {query}'

    @json
    def signup(self):
        return context.form


class DocumentaryTestCase(WSGIDocumentaryTestCase):
    documentary_middleware_factory = ExaminationMiddleware
    controller_factory = Root

    # @staticmethod
    # def application_factory():
    #     return Application(Root())
    #
    def test_basic_pipeline(self):
        response = self.call('Simple pipeline', 'GET', '/')
        self.assertEqual('Content empty', response.text)

        self.assertEqual('Simple pipeline', last_call.title)
        self.assertEqual('/', last_call.url)
        self.assertIsNone(last_call.url_parameters)
        self.assertIsNone(last_call.query_string)
        self.assertIsInstance(last_call.response, Response)
        self.assertEqual('200 OK', last_call.response.status)
        self.assertEqual(200, last_call.response.status_code)
        self.assertEqual('OK', last_call.response.status_text)
        self.assertEqual(b'Content empty', last_call.response.body)
        self.assertEqual('Content empty', last_call.response.text)
        self.assertEqual('text/plain', last_call.response.content_type)
        self.assertEqual('utf-8', last_call.response.encoding)

        self.assertDictEqual(last_call.to_dict(), dict(
            title='Simple pipeline',
            url='/',
            url_parameters=None,
            verb='GET',
            query_string=None,
            form=None,
            role=None,
            expected_status=200,
            description=None,
            response=dict(
                body='Content empty',
                headers=[('Content-Type', 'text/plain; charset=utf-8')],
                status_code=200,
                status_text='OK'
            )
        ))

    def test_url_parameters(self):
        response = self.call('Url parameters 1', 'GET', '/id: 1')
        self.assertEqual('Content 1', response.text)
        self.assertEqual('/1', last_call.url)
        self.assertDictEqual(dict(id='1'), last_call.url_parameters)

        response = self.call('Url parameters 2', 'GET', '/books/isbn: 2')
        self.assertEqual('Book 2', response.text)
        self.assertEqual('/books/2', last_call.url)
        self.assertDictEqual(dict(isbn='2'), last_call.url_parameters)

        response = self.call('Url parameters 3', 'GET', '/books/isbn: 2/name: abc')
        self.assertEqual('Book 2 abc', response.text)
        self.assertEqual('/books/2/abc', last_call.url)
        self.assertDictEqual(dict(isbn='2', name='abc'), last_call.url_parameters)

    def test_query_string(self):
        response = self.call('Query string', 'GET', '/search/books', query=dict(query='abc'))
        self.assertEqual('books abc', response.text)
        self.assertDictEqual(dict(query='abc'), last_call.query_string)

    def test_forms(self):
        response = self.call(
            'Url-encoded form',
            'POST',
            '/signup',
            form=dict(
                field1=1,
                field2=2
            )
        )
        expected_dict = dict(field1='1', field2='2')
        self.assertDictEqual(expected_dict, response.json)
        self.assertDictEqual(expected_dict, last_call.form)
#
# class FileDocumentaryTestCase(WSGIDocumentaryTestCase):
#     documentary_middleware_factory = FileDocumentaryMiddleware
#
#     @staticmethod
#     def application_factory():
#         return Application(Root())
#
#     # TODO: Test call history
#     # TODO: Extract form info from metadata
#     # TODO: Optional role parameter


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
