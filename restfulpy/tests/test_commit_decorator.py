
import unittest

from nanohttp import json, RestController, context, settings
from sqlalchemy import Unicode, Integer

from restfulpy.controllers import JsonPatchControllerMixin
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication


class CommitCheckingModel(DeclarativeBase):
    __tablename__ = 'commit_checking_model'
    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50), unique=True)


class Root(JsonPatchControllerMixin, RestController):

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

    @json
    @commit
    def error(self):
        m = CommitCheckingModel()
        m.title = 'Error'
        DBSession.add(m)
        raise Exception()


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
        self.assertEqual(resp['title'], 'first')
        self.assertEqual(resp['id'], 1)

    def test_commit_decorator_and_json_patch(self):
        # The commit decorator should not to do anything if the request is a jsonpatch.
        self.request('ALL', 'PATCH', '/', doc=False, json=[
            dict(op='post', path='', value=dict(title='second')),
            dict(op='post', path='', value=dict(title='third'))
        ])
        resp, ___ = self.request('ALL', 'GET', '/third', doc=False)
        self.assertEqual(resp['title'], 'third')

    def test_rollback(self):
        self.request('ALL', 'ERROR', '/', doc=False, expected_status=500)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
