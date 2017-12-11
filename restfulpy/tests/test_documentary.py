
import unittest

import webtest
from nanohttp import Application, Controller, text

from restfulpy.documentary import AbstractDocumentaryMiddleware


class ExaminationMiddleware(AbstractDocumentaryMiddleware):
    call = None

    def on_call_done(self, call):
        self.call = call


class Root(Controller):
    @text
    def index(self, id):
        yield str(id)


class DocumentaryTestCase(unittest.TestCase):

    def test_basic_pipeline(self):
        middleware = ExaminationMiddleware(Application(Root()))
        app = webtest.TestApp(middleware)
        response = app.get('/')
        self.assertEqual(response.body, '')
        self.assertDictEqual(
            middleware.call.to_dict(),
            dict(

            )
        )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
