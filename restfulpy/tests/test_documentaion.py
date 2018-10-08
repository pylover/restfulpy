from os import path, mkdir

from bddrest.authoring import response, status
from nanohttp import action, RegexRouteController

from restfulpy.controllers import RootController
from restfulpy.testing import ApplicableTestCase


HERE = path.abspath(path.dirname(__file__))
DATA_DIRECTORY = path.abspath(path.join(HERE, '../../data'))


class Root(RegexRouteController):

    def __init__(self):
        return super().__init__([
            ('/apiv1/documents', self.get), ('/', self.index)
        ])

    @action
    def get(self):
        return 'Index'

    @action
    def index(self):
        return 'Index'


class TestApplication(ApplicableTestCase):
    __controller_factory__ = Root
    __story_directory__ = path.join(DATA_DIRECTORY, 'stories')
    __api_documentation_directory__ = path.join(DATA_DIRECTORY, 'markdown')
    __metadata__ = {
        '/': dict(a=dict(not_none=True, required=True))
    }

    def test_index(self):
        with self.given(
            'There is a / in the title',
            '/apiv1/documents',
            'GET'
        ):
            assert status == 200
            assert response.body == b'Index'

    def test_root_request(self):
        with self.given(
            'Requesting on the root controller',
            '/',
            'INDEX',
            form=dict(a=1)
        ):
            assert status == 200

