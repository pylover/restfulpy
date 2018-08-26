
from bddrest import response, when, Update, status
from nanohttp import json
from sqlalchemy import Unicode, Integer, DateTime, Float, ForeignKey, Boolean, \
    DateTime
from sqlalchemy.ext.associationproxy import association_proxy

from restfulpy.controllers import JsonPatchControllerMixin, ModelRestController
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession, \
    composite, FilteringMixin, PaginationMixin, OrderingMixin, relationship, \
    ModifiedMixin, ActivationMixin, synonym
from restfulpy.testing import ApplicableTestCase


class Metting(DeclarativeBase):
    __tablename__ = 'metting'
    id = Field(Integer, primary_key=True)
    when = Field(DateTime)


class Root(JsonPatchControllerMixin, ModelRestController):
    __model__ = 'metting'

    @json
    @commit
    def post(self):
        m = Metting()
        m.update_from_request()
        DBSession.add(m)
        return m.when.isoformat()


class TestBaseModel(ApplicableTestCase):
    __controller_factory__ = Root

    def test_update_from_request(self):
        with self.given(
            'Posting a datetime in form',
            verb='POST',
            form=dict(
                when='2001-01-01T00:01',
            )
        ):
            assert status == 200
            assert response.json == '2001-01-01T00:01:00'

            when(
                'Posting a date instead of datetime',
                form=dict(
                    when='2001-01-01'
                )
            )

            assert status == 200
            assert response.json == '2001-01-01T00:00:00'

            when(
                'Posting an invalid datetime',
                form=dict(
                    when='2001-00-01'
                )
            )

            assert status == '400 Invalid date or time format'

