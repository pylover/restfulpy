
import unittest

from nanohttp import Application, Controller, text

from restfulpy.documentary import AbstractDocumentaryMiddleware, WSGIDocumentaryTestCase, Response


last_call = None


class ExaminationMiddleware(AbstractDocumentaryMiddleware):
    def on_call_done(self, call):
        global last_call
        last_call = call


class Root(Controller):
    @text
    def index(self, id_='empty'):
        yield f'Content {id_}'


class DocumentaryTestCase(WSGIDocumentaryTestCase):
    documentary_middleware_factory = ExaminationMiddleware

    @staticmethod
    def application_factory():
        return Application(Root())

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
            response=dict(
                body=b'Content empty',
                headers=[('Content-Type', 'text/plain; charset=utf-8')],
                status_code=200,
                status_text='OK'
            )
        ))

    # TODO: Test url params
    # TODO: Test query strings
    # TODO: Test call history
    #
    # def test_basic_pipeline(self):
    #     response = self.call('Simple pipeline', 'GET', '/id: 1')
    #     self.assertEqual('Content 1', response.text)
    #
    #     self.assertDictEqual(last_call.to_dict(), dict(
    #         title='Simple pipeline',
    #         url='/1',
    #         url_parameters=dict(
    #             id='1'
    #         ),
    #         verb='GET',
    #         query_string={},
    #         response=dict(
    #             body=b'Content 1',
    #             headers=[('Content-Type', 'text/plain; charset=utf-8')],
    #             status='200 OK'
    #         )
    #     ))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
