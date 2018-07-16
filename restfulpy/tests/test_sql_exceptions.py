from bddrest.authoring import response
from nanohttp import json
from sqlalchemy import Unicode, Integer

from restfulpy.controllers import JsonPatchControllerMixin, ModelRestController
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession, \
    FilteringMixin, PaginationMixin, OrderingMixin, ModifiedMixin
from restfulpy.testing import ApplicableTestCase


class SqlErrorCheckingModel(
    ModifiedMixin,
    FilteringMixin,
    PaginationMixin,
    OrderingMixin,
    DeclarativeBase
):
    __tablename__ = 'sql_error_checking_model'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50), unique=True, nullable=False)


class Root(JsonPatchControllerMixin, ModelRestController):
    __model__ = SqlErrorCheckingModel

    @json
    @commit
    def post(self):
        m = SqlErrorCheckingModel()
        m.update_from_request()
        DBSession.add(m)
        return m

    @json
    @SqlErrorCheckingModel.expose
    def get(self, title: str=None):
        query = SqlErrorCheckingModel.query
        if title:
            return query.filter(SqlErrorCheckingModel.title == title)\
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

        return
        # unique_violation
        request(
            'ALL',
            'POST',
            '/',
            params=dict(title='test'),
            expected_status='''409 unique_violation ERROR:  duplicate\
            key value violates unique constraint \
            "sql_error_checking_model_title_key"\nDETAIL:\
            Key (title)=(test) already exists.\n''',
        )

