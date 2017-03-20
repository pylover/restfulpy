
import unittest

from nanohttp import action, Controller

from restfulpy.testing import WebAppTestCase
from restfulpy.application import Application


class MockupApplication(Application):
    builtin_configuration = '''
    db:
      test_uri: postgresql://postgres:postgres@localhost/lemur_test
      administrative_uri: postgresql://postgres:postgres@localhost/postgres
    '''

    def configure(self, files=None, context=None, **kwargs):
        _context = dict(
            process_name='restfulpy_unittests'
        )
        if context:
            _context.update(context)
        super().configure(files=files, context=_context, **kwargs)


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
