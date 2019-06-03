from bddrest.authoring import response
from nanohttp import action

from restfulpy.controllers import RootController
from restfulpy.testing import ApplicableTestCase
from restfulpy import Application as RestfulpyApplication


class Root(RootController):

    @action
    def index(self):
        return 'Index'


foo = RestfulpyApplication('Foo', Root())


class TestApplication(ApplicableTestCase):
    __application__ = foo

    def test_index(self):
        with self.given('Test application root', '/', 'GET'):
            assert response.body == b'Index'
            assert response.status == '200 OK'

    def test_options(self):
        with self.given('Test OPTIONS verb', '/', 'OPTIONS'):
            assert response.headers['Cache-Control'] == 'no-cache,no-store'

    def test_application_configure(self):
        foo.configure(force=True, context={'a': 1})
