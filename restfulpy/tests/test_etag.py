import unittest

from sqlalchemy import Unicode
from nanohttp import settings, json, etag, context

from restfulpy.orm import DeclarativeBase, DBSession, Field, ModifiedMixin, commit
from restfulpy.testing import WebAppTestCase, FormParameter
from restfulpy.tests.helpers import MockupApplication
from restfulpy.controllers import ModelRestController


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
        query = EtagCheckingModel.query
        if title:
            return query.filter(EtagCheckingModel.title == title).one_or_none()
        return query

    @json
    @etag
    @EtagCheckingModel.expose
    @commit
    def put(self, title: str=None):
        m = DBSession.query(EtagCheckingModel).filter(EtagCheckingModel.title == title).one_or_none()
        m.update_from_request()
        context.etag_match(m.__etag__)
        return m


class EtagCheckingModelTestCase(WebAppTestCase):
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

    def test_etag_match(self):
        resp, headers = self.request('ALL', 'POST', '/', params=[
            FormParameter('title', 'etag_test')
        ])
        self.assertIn('ETag', headers)
        initial_etag = headers['ETag']

        # Getting the resource with known etag, expected 304
        self.request(
            'ALL', 'GET', '/etag_test',
            headers={
                'If-None-Match': initial_etag
            },
            expected_status=304
        )

        # Putting without the etag header, expected error: Precondition Failed
        self.request(
            'ALL', 'PUT', '/etag_test',
            params=[
                FormParameter('title', 'etag_test_edit1')
            ],
            expected_status=412
        )

        # Putting with the etag header, expected: success
        resp, headers = self.request(
            'ALL', 'PUT', '/etag_test',
            params=[
                FormParameter('title', 'etag_test_edit1')
            ],
            headers={
                'If-Match': initial_etag
            }
        )
        self.assertIn('ETag', headers)
        etag_after_put = headers['ETag']
        self.assertNotEqual(initial_etag, etag_after_put)

        # Getting the resource with known etag, expected 304
        self.request(
            'ALL', 'GET', '/etag_test_edit1',
            headers={
                'If-None-Match': initial_etag
            },
            expected_status=200
        )
        self.assertIn('ETag', headers)
        new_etag = headers['ETag']
        self.assertNotEqual(new_etag, initial_etag)
        self.assertEqual(new_etag, etag_after_put)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
