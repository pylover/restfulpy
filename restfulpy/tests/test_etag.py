from bddrest import response, when
from nanohttp import json, etag, context
from sqlalchemy import Unicode

from restfulpy.controllers import ModelRestController
from restfulpy.orm import DeclarativeBase, DBSession, Field, ModifiedMixin,\
    commit
from restfulpy.testing import ApplicableTestCase


class EtagCheckingModel(ModifiedMixin, DeclarativeBase):
    __tablename__ = 'etag_checking_model'

    title = Field(Unicode(50), primary_key=True)

    @property
    def __etag__(self):
        return self.last_modification_time.isoformat()


class Root(ModelRestController):
    __model__ = EtagCheckingModel

    @json
    @etag
    @commit
    def post(self):
        m = EtagCheckingModel()
        m.update_from_request()
        DBSession.add(m)
        return m

    @json
    @etag
    @EtagCheckingModel.expose
    def get(self, title: str=None):
        query = DBSession.query(EtagCheckingModel)
        if title:
            return query.filter(EtagCheckingModel.title == title).one_or_none()
        return query

    @json
    @etag
    @EtagCheckingModel.expose
    @commit
    def put(self, title: str=None):
        m = DBSession.query(EtagCheckingModel)\
            .filter(EtagCheckingModel.title == title).one_or_none()
        m.update_from_request()
        context.etag_match(m.__etag__)
        return m


class TestEtagCheckingModel(ApplicableTestCase):
    __controller_factory__ = Root

    def test_etag_match(self):
        with self.given(
            'Posting a simple form to enusre ETag header',
            verb='POST',
            form=dict(title= 'etag_test')
        ):
            assert 'ETag' in response.headers

            initial_etag = response.headers['ETag']

        with self.given(
            'Getting the resource with known etag, expected 304',
            url='/etag_test',
            headers={
                'If-None-Match': initial_etag
            }):
            assert response.status == 304

        with self.given(
                'Putting without the etag header',
                '/etag_test',
                'PUT',
                form=dict(title='etag_test_edit1'),
            ):
            assert response.status == 412

            when(
                'Putting with the etag header, expected: success',
                headers={'If-Match': initial_etag}
            )
            assert 'ETag' in response.headers
            etag_after_put = response.headers['ETag']
            assert initial_etag != etag_after_put

        with self.given(
                'Getting the resource with known etag',
                '/etag_test_edit1',
                headers={
                    'If-None-Match': initial_etag
                },
            ):
            assert response.status == 200
            assert 'ETag' in response.headers
            new_etag = response.headers['ETag']
            assert new_etag != initial_etag
            assert new_etag == etag_after_put

