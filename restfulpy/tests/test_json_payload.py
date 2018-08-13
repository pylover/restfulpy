from bddrest.authoring import response
from nanohttp import json, Controller, context

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
            json=payload,
        ):
            assert response.json ==  payload

