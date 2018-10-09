from bddrest import response, status, when
from nanohttp import json, Controller, settings

from restfulpy.testing import ApplicableTestCase


class Root(Controller):

    @json
    def index(self):
        return 'index'


class TestServerTimestamp(ApplicableTestCase):
    __controller_factory__ = Root

    @classmethod
    def configure_application(self):
        super().configure_application()
        settings.merge('timestamp: true')

    def test_server_timestamp_header(self):
        with self.given('Geting server\'s timestamp'):
            assert status == 200
            assert 'X-Server-Timestamp' in response.headers

            settings.merge('timestamp: false')
            when('With default configuration')
            assert status == 200
            assert 'X-Server-Timestamp' not in response.headers

