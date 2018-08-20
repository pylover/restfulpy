from datetime import datetime

from nanohttp.contexts import Context
from sqlalchemy import Integer, Unicode, DateTime
from sqlalchemy.orm import synonym

from restfulpy.orm import DeclarativeBase, Field, OrderingMixin


class OrderingObject(OrderingMixin, DeclarativeBase):
    __tablename__ = 'orderable_ordering_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))
    _age = Field(Integer)
    created_at = Field(
        DateTime,
        nullable=False,
        json='createdAt',
        readonly=True,
        default=datetime.utcnow,
    )

    def _set_age(self, age):
        self._age = age

    def _get_age(self):  # pragma: no cover
        return self._age

    age = synonym('_age', descriptor=property(_get_age, _set_age))


def test_ordering_mixin(db):
    session =db()

    for i in range(1, 6):
        obj = OrderingObject(
            title=f'object {6-i//2}',
            age=i * 10,
        )
        session.add(obj)

    session.commit()

    query = session.query(OrderingObject)

    # Ascending
    with Context({'QUERY_STRING': 'sort=id'}):
        result = OrderingObject.sort_by_request(query).all()
        assert result[0].id == 1
        assert result[-1].id == 5

    # Descending
    with Context({'QUERY_STRING': 'sort=-id'}):
        result = OrderingObject.sort_by_request(query).all()
        assert result[0].id == 5
        assert result[-1].id == 1

    # Sort by Synonym Property
    with Context({'QUERY_STRING': 'sort=age'}):
        result = OrderingObject.sort_by_request(query).all()
        assert result[0].id == 1
        assert result[-1].id == 5

    # Mutiple sort criteria
    with Context({'QUERY_STRING': 'sort=title,id'}):
        result = OrderingObject.sort_by_request(query).all()
        assert result[0].id == 4
        assert result[1].id == 5

        assert result[2].id == 2
        assert result[3].id == 3

        assert result[4].id == 1

    # Sort by date
    with Context({'QUERY_STRING': 'sort=-createdAt'}):
        result = OrderingObject.sort_by_request(query).all()
        assert result[0].id == 5
        assert result[1].id == 4
        assert result[2].id == 3
        assert result[3].id == 2
        assert result[4].id == 1

