from tempfile import mktemp

from bddrest.authoring import response
from nanohttp import action, settings

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
        foo.configure(context={'a': 1}, force=True)
        assert settings.debug == True

    def test_application_configure_file(self):
        filename = mktemp()
        content = b'foo:\n  bar: baz\n'

        with open(filename, 'wb') as f:
            f.write(content)

        foo.configure(filename=filename, force=True)
        assert settings.foo.bar == 'baz'

    def test_application_configure_encrypted_file(self):
        filename = mktemp()
        content = b'foo:\n  bar: baz\n'
        content = foo.__configuration_cipher__.encrypt(content)
        with open(filename, 'wb') as f:
            f.write(b'#enc')
            f.write(content)

        foo.configure(filename=filename, context={'a': 1}, force=True)
        assert settings.foo.bar == 'baz'

