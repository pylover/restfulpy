
import unittest
from os.path import dirname, abspath, join

from nanohttp import action

from restfulpy.controllers import RootController
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication


HERE = abspath(dirname(__file__))
DATA_DIR = join(HERE, 'data')


class Root(RootController):

    @action
    def index(self):
        return 'Index'


class ApplicationTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', Root())

    def test_index(self):
        response, headers = self.request('ALL', 'GET', '/')
        self.assertEqual(response, b'Index')

    def test_options(self):
        response, headers = self.request('ALL', 'OPTIONS', '/')
        self.assertEqual(headers['Cache-Control'], 'no-cache,no-store')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
