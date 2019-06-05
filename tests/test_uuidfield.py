import uuid

from bddrest import response
from nanohttp import json
from sqlalchemy.dialects.postgresql import UUID

from restfulpy.controllers import JsonPatchControllerMixin, ModelRestController
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession
from restfulpy.testing import ApplicableTestCase, Uuid1Freeze


def new_uuid():
    return uuid.uuid1()


class Uuid1Model(DeclarativeBase):

    __tablename__ = 'uuid1'

    id = Field(UUID(as_uuid=True), primary_key=True, default=new_uuid)


class Root(JsonPatchControllerMixin, ModelRestController):
    __model__ = Uuid1Model

    @json
    @commit
    def get(self):
        u = Uuid1Model()
        DBSession.add(u)
        return u


class TestUuidField(ApplicableTestCase):
    __controller_factory__ = Root

    def test_uuid1(self):
        frozen_uuid_str = 'ce52b1ee602a11e9a721b06ebfbfaee7'
        frozen_uuid = uuid.UUID(frozen_uuid_str)
        with Uuid1Freeze(frozen_uuid), self.given('testing uuid'):
            assert response.json['id'] == frozen_uuid_str

