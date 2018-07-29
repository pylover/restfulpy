from bddrest import response, status
from nanohttp import json
from sqlalchemy import Unicode, Integer

from restfulpy.controllers import ModelRestController
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession
from restfulpy.testing import ApplicableTestCase


class Foo(DeclarativeBase):
    __tablename__ = 'foo'
    id = Field(Integer, primary_key=True)
    title = Field(Unicode(10))


class Root(ModelRestController):
    __model__ = Foo

    @json
    @commit
    @Foo.expose
    def post(self):
        m = Foo()
        m.update_from_request()
        DBSession.add(m)
        return m

    @json
    @Foo.expose
    def get(self):
        return DBSession.query(Foo).first()


class TestStringEncoding(ApplicableTestCase):
    __controller_factory__ = Root

    def test_string_codec(self):
        with self.given(
            'Title Has a backslash',
            verb='POST',
            form=dict(title='\\'),
        ):
            assert status == 200
            assert response.json['title'] == '\\'

        with self.given(
            'Getting foo',
            verb='GET',
        ):
            title = response.json['title']
            assert status == 200
            assert title == '\\'
            assert len(title) == 1
