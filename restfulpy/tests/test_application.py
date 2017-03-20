
import unittest

from nanohttp import action, Controller

from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication


class Root(Controller):

    @action
    def index(self):
        return 'Index'


class ApplicationTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', Root())

    def test_index(self):
        response, headers = self.request('ALL', 'GET', '/')
        self.assertEqual(response, b'Index')


if __name__ == '__main__':
    unittest.main()
