
import unittest

from nanohttp import json, RestController, context, settings
from sqlalchemy import Unicode

from restfulpy.orm import commit, DeclarativeBase, Field, DBSession
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication


class CommitCheckingModel(DeclarativeBase):
    __tablename__ = 'commit_checking_model'
    title = Field(Unicode(50), primary_key=True)


class Root(RestController):

    @json
    @commit
    def post(self):
        m = CommitCheckingModel()
        m.title = context.form['title']
        DBSession.add(m)
        return m

    @json
    def get(self, title: str=None):
        m = DBSession.query(CommitCheckingModel).filter(CommitCheckingModel.title == title).one()
        return m


class CommitDecoratorTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', Root())
    __configuration__ = '''
    db:
      uri: sqlite://    # In memory DB
      echo: false
    '''

    @classmethod
    def configure_app(cls):
        cls.application.configure(force=True)
        settings.merge(cls.__configuration__)

    def test_commit_decorator(self):
        self.request('ALL', 'POST', '/', params=dict(title='first'), doc=False)
        resp, ___ = self.request('ALL', 'GET', '/first', doc=False)
        self.assertEquals(resp['title'], 'first')


if __name__ == '__main__':
    unittest.main()
