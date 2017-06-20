import unittest

from sqlalchemy import Integer, Unicode
from nanohttp import settings, HttpBadRequest
from nanohttp.contexts import Context

from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.orm import DeclarativeBase, Field, DBSession, PaginationMixin


class PagingObject(PaginationMixin, DeclarativeBase):
    __tablename__ = 'paging_object'
    __max_take__ = 4

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))


class PaginationMixinTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', None)
    __configuration__ = '''
    db:
      uri: sqlite://    # In memory DB
      echo: false
    '''

    @classmethod
    def configure_app(cls):
        cls.application.configure(force=True)
        settings.merge(cls.__configuration__)

    def test_pagination_mixin(self):
        for i in range(1, 6):
            # noinspection PyArgumentList
            obj = PagingObject(
                title='object %s' % i,
            )
            DBSession.add(obj)
        DBSession.commit()

        with Context({'QUERY_STRING': 'take=2&skip=1'}, self.application) as context:
            self.assertEqual(PagingObject.paginate_by_request().count(), 2)
            self.assertEqual(context.response_headers['X-Pagination-Take'], '2')
            self.assertEqual(context.response_headers['X-Pagination-Skip'], '1')
            self.assertEqual(context.response_headers['X-Pagination-Count'], '5')

        with Context({'QUERY_STRING': 'take=two&skip=one'}, self.application):
            self.assertEqual(PagingObject.paginate_by_request().count(), 4)

        with Context({'QUERY_STRING': 'take=5'}, self.application):
            self.assertRaises(HttpBadRequest, PagingObject.paginate_by_request)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
