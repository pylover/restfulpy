
from nanohttp import json, Controller, context
from bddrest.authoring import response

from restfulpy.testing import ApplicableTestCase


class Root(Controller):

    @json
    def index(self):
        return context.form


class TestJSONPayload(ApplicableTestCase):
    __controller_factory__ = Root

    def test_index(self):
        payload = dict(
            a=1,
            b=2
        )

        with self.given(
            'Testing json pyload',
            form=payload,
            content_type='application/json'
        ):
            assert response.json ==  payload

