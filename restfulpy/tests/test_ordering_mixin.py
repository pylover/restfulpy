import unittest
from datetime import datetime

from sqlalchemy import Integer, Unicode, DateTime
from sqlalchemy.orm import synonym
from nanohttp import settings
from nanohttp.contexts import Context

from restfulpy.tests.helpers import WebAppTestCase
from restfulpy.testing import MockupApplication
from restfulpy.orm import DeclarativeBase, Field, DBSession, OrderingMixin


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


class OrderingMixinTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', None)
    __configuration__ = '''
    db:
      url: sqlite://    # In memory DB
      echo: false
    '''

    @classmethod
    def configure_app(cls):
        cls.application.configure(force=True)
        settings.merge(cls.__configuration__)

    def test_ordering_mixin(self):
        for i in range(1, 6):
            # noinspection PyArgumentList
            obj = OrderingObject(
                title=f'object {6-i//2}',
                age=i * 10,
            )
            DBSession.add(obj)

        DBSession.commit()

        # Ascending
        with Context({'QUERY_STRING': 'sort=id'}, self.application):
            result = OrderingObject.sort_by_request().all()
            self.assertEqual(result[0].id, 1)
            self.assertEqual(result[-1].id, 5)

        # Descending
        with Context({'QUERY_STRING': 'sort=-id'}, self.application):
            result = OrderingObject.sort_by_request().all()
            self.assertEqual(result[0].id, 5)
            self.assertEqual(result[-1].id, 1)

        # Sort by Synonym Property
        with Context({'QUERY_STRING': 'sort=age'}, self.application):
            result = OrderingObject.sort_by_request().all()
            self.assertEqual(result[0].id, 1)
            self.assertEqual(result[-1].id, 5)

        # Mutiple sort criteria
        with Context({'QUERY_STRING': 'sort=title,id'}, self.application):
            result = OrderingObject.sort_by_request().all()
            self.assertEqual(result[0].id, 4)
            self.assertEqual(result[1].id, 5)

            self.assertEqual(result[2].id, 2)
            self.assertEqual(result[3].id, 3)

            self.assertEqual(result[4].id, 1)

        # Sort by date
        with Context({'QUERY_STRING': 'sort=-createdAt'}, self.application):
            result = OrderingObject.sort_by_request().all()
            self.assertEqual(result[0].id, 5)
            self.assertEqual(result[1].id, 4)
            self.assertEqual(result[2].id, 3)
            self.assertEqual(result[3].id, 2)
            self.assertEqual(result[4].id, 1)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
