from bddrest.authoring import response
from nanohttp import action

from restfulpy.controllers import RootController
from restfulpy.testing import ApplicableTestCase


class Root(RootController):

    @action
    def index(self):
        return 'Index'


class TestApplication(ApplicableTestCase):
    __controller_factory__ = Root

    def test_index(self):
        with self.given('Test application root', '/', 'GET'):
            assert response.status == '200 OK'
            assert response.body == b'Index'

    def test_options(self):
        with self.given('Test OPTIONS verb', '/', 'OPTIONS'):
            assert response.headers['Cache-Control'] == 'no-cache,no-store'

