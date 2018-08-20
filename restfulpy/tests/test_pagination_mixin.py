import pytest
from nanohttp import HTTPBadRequest
from nanohttp.contexts import Context
from sqlalchemy import Integer, Unicode

from restfulpy.orm import DeclarativeBase, Field, PaginationMixin


class PagingObject(PaginationMixin, DeclarativeBase):
    __tablename__ = 'paging_object'
    __max_take__ = 4

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))


def test_pagination_mixin(db):
    session = db()

    for i in range(1, 6):
        obj = PagingObject(
            title='object %s' % i,
        )
        session.add(obj)
    session.commit()

    query = session.query(PagingObject)

    with Context({'QUERY_STRING': 'take=2&skip=1'}) as context:
        assert PagingObject.paginate_by_request(query).count() == 2
        assert context.response_headers['X-Pagination-Take'] == '2'
        assert context.response_headers['X-Pagination-Skip'] == '1'
        assert context.response_headers['X-Pagination-Count'] == '5'

    with Context({'QUERY_STRING': 'take=two&skip=one'}), \
        pytest.raises(HTTPBadRequest):
        PagingObject.paginate_by_request(query).count()

    with Context({'QUERY_STRING': 'take=5'}), pytest.raises(HTTPBadRequest):
        PagingObject.paginate_by_request(query)

