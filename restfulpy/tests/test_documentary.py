
import unittest

from nanohttp import Application, Controller, text

from restfulpy.documentary import AbstractDocumentaryMiddleware, WSGIDocumentaryTestCase


last_call = None


class ExaminationMiddleware(AbstractDocumentaryMiddleware):
    def on_call_done(self, call):
        global last_call
        last_call = call


class Root(Controller):
    @text
    def index(self, id=None):
        yield id


class DocumentaryTestCase(WSGIDocumentaryTestCase):
    documentary_middleware_factory = ExaminationMiddleware

    @staticmethod
    def application_factory():
        return Application(Root())

    def test_basic_pipeline(self):
        response = self.call('Simple pipeline', 'GET', '/id: 1')
        self.assertEqual('1', response.text)

        self.assertDictEqual(last_call.to_dict(), dict(
            title='Simple pipeline',
            url='/1',
            verb='GET',
            query_string={},
            response='1'
        ))
        # self.assertDictEqual(last_call.url_params, ['id'])
        # self.assertDictEqual(
        #     last_call.to_dict(),
        #     dict(
        #
        #     )
        # )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
