from bddrest import response, when
from nanohttp import json, RestController, context
from nanohttp.exceptions import HTTPSuccess, HTTPFound
from sqlalchemy import Unicode, Integer

from restfulpy.controllers import JsonPatchControllerMixin
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession
from restfulpy.testing import ApplicableTestCase


class Bar(DeclarativeBase):
    __tablename__ = 'bar'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50), unique=True)


class Root(JsonPatchControllerMixin, RestController):

    @json
    @commit
    def create(self):
        bar = Bar(title=context.form['title'])
        DBSession.add(bar)

        if bar.title == 'success':
            raise HTTPSuccess()

        elif bar.title == 'redirect':
            raise HTTPFound(location='/fake/location')

        return bar

    @json
    @commit
    def error(self):
        bar = Bar(title='Error')
        DBSession.add(bar)
        raise Exception()


class TestCommitDecorator(ApplicableTestCase):
    __controller_factory__ = Root

    def test_commit_decorator(self):
        with self.given(
            'Testing the operation of commit decorator',
            verb='CREATE',
            form=dict(title='first')
        ):
            assert self.create_session().query(Bar) \
                .filter(Bar.title == 'first') \
                .one_or_none()

    def test_commit_decorator_and_json_patch(self):
        with self.given(
            'The commit decorator should not to do anything if the request '
                'is a jsonpatch.',
            verb='PATCH',
            json=[
                dict(op='create', path='', value=dict(title='second')),
                dict(op='create', path='', value=dict(title='third')),
            ],
        ):
            assert self.create_session().query(Bar) \
                .filter(Bar.title == 'third') \
                .one_or_none()

    def test_rollback(self):
        with self.given('Raise exception', verb='ERROR'):
            assert response.status == 500

    def test_commit_on_raise_http_success(self):
        with self.given(
            'Testing the operation of commit decorator on raise 2xx',
            verb='CREATE',
            form=dict(title='success')
        ):
            assert self.create_session().query(Bar) \
                .filter(Bar.title == 'success') \
                .one_or_none()

    def test_commit_on_raise_http_redirect(self):
        with self.given(
            'Testing the operation of commit decorator on raise 3xx',
            verb='CREATE',
            form=dict(title='redirect')
        ):
            assert self.create_session().query(Bar) \
                .filter(Bar.title == 'redirect') \
                .one_or_none()

