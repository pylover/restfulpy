from restfulpy.orm import DeclarativeBase, Field, FilteringMixin, \
    PaginationMixin, OrderingMixin, ModifiedMixin
from sqlalchemy import Unicode, Integer


class Foo(FilteringMixin, PaginationMixin, OrderingMixin, ModifiedMixin,
          DeclarativeBase):
    __tablename__ = 'foo'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(100), unique=True)

