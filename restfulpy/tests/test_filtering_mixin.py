import pytest
from nanohttp import HTTPBadRequest
from nanohttp.contexts import Context
from sqlalchemy import Integer, Unicode

from restfulpy.orm import DeclarativeBase, Field, FilteringMixin


class FilteringObject(FilteringMixin, DeclarativeBase):
    __tablename__ = 'filtering_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))


def test_filtering_mixin(db):
    session = db()

    for i in range(1, 6):
        session.add(FilteringObject(
            title='object %s' % i,
        ))

    session.add(FilteringObject(
        title='A simple title',
    ))
    session.commit()

    query = session.query(FilteringObject)

    with Context({'QUERY_STRING': 'id=1'}) as context, \
            pytest.raises(HTTPBadRequest):
        context.query['id'] = 1
        FilteringObject.filter_by_request(query)

    # IN
    with Context({'QUERY_STRING': 'id=IN(1,2,3)'}):
        assert FilteringObject.filter_by_request(query).count() == 3

    # NOT IN
    with Context({'QUERY_STRING': 'id=!IN(1,2,3)'}):
        assert FilteringObject.filter_by_request(query).count() == 3

    # IN (error)
    with Context({'QUERY_STRING': 'id=IN()'}), \
        pytest.raises(HTTPBadRequest):
        FilteringObject.filter_by_request(query)

    # Between
    with Context({'QUERY_STRING': 'id=BETWEEN(1,3)'}):
        assert FilteringObject.filter_by_request(query).count() == 3

    # IS NULL
    with Context({'QUERY_STRING': 'title=null'}):
        assert FilteringObject.filter_by_request(query).count() == 0

    # IS NOT NULL
    with Context({'QUERY_STRING': 'title=!null'}):
        assert FilteringObject.filter_by_request(query).count() == 6

    # ==
    with Context({'QUERY_STRING': 'id=1'}):
        assert FilteringObject.filter_by_request(query).count() == 1

    # !=
    with Context({'QUERY_STRING': 'id=!1'}):
        assert FilteringObject.filter_by_request(query).count() == 5

    # >=
    with Context({'QUERY_STRING': 'id=>=2'}):
        assert FilteringObject.filter_by_request(query).count() == 5

    # >
    with Context({'QUERY_STRING': 'id=>2'}):
        assert FilteringObject.filter_by_request(query).count() == 4

    # <=
    with Context({'QUERY_STRING': 'id=<=3'}):
        FilteringObject.filter_by_request(query).count() == 3

    # <
    with Context({'QUERY_STRING': 'id=<3'}):
        assert FilteringObject.filter_by_request(query).count() == 2

    # LIKE
    with Context({'QUERY_STRING': 'title=%obj%'}):
        assert FilteringObject.filter_by_request(query).count() == 5

    with Context({'QUERY_STRING': 'title=%OBJ%'}):
        assert FilteringObject.filter_by_request(query).count() == 0

    # ILIKE
    with Context({'QUERY_STRING': 'title=~%obj%'}):
        assert FilteringObject.filter_by_request(query).count() == 5

    with Context({'QUERY_STRING': 'title=~%OBJ%'}):
        assert FilteringObject.filter_by_request(query).count() == 5

    with Context({'QUERY_STRING': 'title=A sim%'}):
        assert FilteringObject.filter_by_request(query).count() == 1

    with Context({'QUERY_STRING': 'title=%25ect 5'}):
        assert FilteringObject.filter_by_request(query).count() == 1

    with Context({'QUERY_STRING': 'title=%imple%'}):
        assert FilteringObject.filter_by_request(query).count() == 1

    with Context({'QUERY_STRING': 'title=~%IMPLE%'}):
        assert FilteringObject.filter_by_request(query).count() == 1
