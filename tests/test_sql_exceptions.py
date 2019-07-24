from bddrest import response, when, status
from nanohttp import json
from sqlalchemy import Unicode, Integer

from restfulpy.controllers import JSONPatchControllerMixin, ModelRestController
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession, \
    FilteringMixin, PaginationMixin, OrderingMixin, ModifiedMixin
from restfulpy.testing import ApplicableTestCase
from restfulpy.exceptions import SQLError


class SQLErrorCheckingModel(
    ModifiedMixin,
    FilteringMixin,
    PaginationMixin,
    OrderingMixin,
    DeclarativeBase
):
    __tablename__ = 'sql_error_checking_model'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50), unique=True, nullable=False)


class Root(ModelRestController):
    __model__ = SQLErrorCheckingModel

    @json
    @commit
    def post(self):
        m = SQLErrorCheckingModel()
        m.update_from_request()
        DBSession.add(m)
        return m

    @json
    @SQLErrorCheckingModel.expose
    def get(self, title: str=None):
        query = SQLErrorCheckingModel.query
        if title:
            return query.filter(SQLErrorCheckingModel.title == title)\
                .one_or_none()
        return query


class TestSqlExceptions(ApplicableTestCase):
    __controller_factory__ = Root

    def test_sql_errors(self):
        with self.given(
                'Testing SQL exceptions',
                '/',
                'POST',
                form=dict(title='test')
            ):
            assert response.json['title'] == 'test'

            when('Posting gain to raise a unique_violation sql error')
            assert status == 409

    def test_invalid_sql_error(self):
        assert '500 Internal server error' == SQLError.map_exception(ValueError())

