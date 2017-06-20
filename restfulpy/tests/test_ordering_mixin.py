import unittest

from sqlalchemy import Integer, Unicode
from sqlalchemy.orm import synonym

from nanohttp import settings
from nanohttp.contexts import Context

from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.orm import DeclarativeBase, Field, DBSession, OrderingMixin, OrderableMixin


class OrderableOrderingObject(OrderableMixin, OrderingMixin, DeclarativeBase):
    __tablename__ = 'orderable_ordering_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))
    _age = Field(Integer)

    def _set_age(self, age):
        self._age = age

    def _get_age(self):  # pragma: no cover
        return self._age

    age = synonym('_age', descriptor=property(_get_age, _set_age))


class OrderingObject(OrderingMixin, DeclarativeBase):
    __tablename__ = 'ordering_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))


class OrderingMixinTestCase(WebAppTestCase):
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

    def test_ordering_mixin(self):
        for i in range(1, 6):
            # noinspection PyArgumentList
            obj = OrderableOrderingObject(title='object %s' % i, age=i * 10)
            DBSession.add(obj)

            # noinspection PyArgumentList
            obj = OrderingObject(title='object %s' % i,)
            DBSession.add(obj)
        DBSession.commit()

        # Default soring with Orderable objects
        with Context({'QUERY_STRING': ''}, self.application):
            result = OrderableOrderingObject.sort_by_request().all()
            self.assertEqual(result[0].id, 1)
            self.assertEqual(result[-1].id, 5)

        # Default soring without Orderable objects
        with Context({'QUERY_STRING': ''}, self.application):
            result = OrderingObject.sort_by_request().all()
            self.assertEqual(len(result), 5)

        # Ascending
        with Context({'QUERY_STRING': 'sort=id'}, self.application):
            result = OrderableOrderingObject.sort_by_request().all()
            self.assertEqual(result[0].id, 1)
            self.assertEqual(result[-1].id, 5)

        # Descending
        with Context({'QUERY_STRING': 'sort=-id'}, self.application):
            result = OrderableOrderingObject.sort_by_request().all()
            self.assertEqual(result[0].id, 5)
            self.assertEqual(result[-1].id, 1)

        # Sort by Synonym Property
        with Context({'QUERY_STRING': 'sort=age'}, self.application):
            result = OrderableOrderingObject.sort_by_request().all()
            self.assertEqual(result[0].id, 1)
            self.assertEqual(result[-1].id, 5)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
