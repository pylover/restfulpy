
import unittest

from nanohttp import json, Controller, context

from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication


class Root(Controller):

    @json
    def index(self):
        return context.form


class JSONPayloadTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', Root())

    def test_index(self):
        payload = dict(
            a=1,
            b=2
        )
        response, headers = self.request('ALL', 'GET', '/', json=payload)
        self.assertDictEqual(response, payload)


if __name__ == '__main__':
    unittest.main()
