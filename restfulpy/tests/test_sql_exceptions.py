import unittest

from nanohttp import json, settings
from sqlalchemy import Unicode, Integer

from restfulpy.controllers import JsonPatchControllerMixin, ModelRestController
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession, FilteringMixin, PaginationMixin, OrderingMixin, \
    ModifiedMixin
from restfulpy.tests.helpers import WebAppTestCase
from restfulpy.testing import MockupApplication


class SqlErrorCheckingModel(ModifiedMixin, FilteringMixin, PaginationMixin, OrderingMixin, DeclarativeBase):
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
            return query.filter(SqlErrorCheckingModel.title == title).one_or_none()
        return query


class SqlExceptionsTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', Root())
    __configuration__ = '''
    db:
      url: sqlite://    # In memory DB
      echo: false
    '''

    @classmethod
    def configure_app(cls):
        cls.application.configure(force=True)
        settings.merge(cls.__configuration__)

    def test_sql_errors(self):
        resp, ___ = self.request('ALL', 'POST', '/', params=dict(title='test'))
        self.assertEqual(resp['title'], 'test')

        self.max_diff = None
        # unique_violation
        self.request(
            'ALL',
            'POST',
            '/',
            params=dict(title='test'),
            expected_status=r'''409 unique_violation ERROR:  duplicate key value violates unique constraint "sql_error_checking_model_title_key"\nDETAIL:  Key (title)=(test) already exists.\n''',
        )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
