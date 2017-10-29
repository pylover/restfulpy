import unittest

from sqlalchemy import Unicode
from nanohttp import settings

from restfulpy.orm import DeclarativeBase, DBSession, Field, OrderableMixin
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication


class OrderableCheckingModel(OrderableMixin, DeclarativeBase):
    __tablename__ = 'orderable_checking_model'

    title = Field(Unicode(50), primary_key=True)


class OrderableCheckingModelTestCase(WebAppTestCase):
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

    def test_orderable_mixin(self):

        for i in range(3):
            # noinspection PyArgumentList
            instance = OrderableCheckingModel(
                title='test title %s' % i,
                order=i
            )
            DBSession.add(instance)
            DBSession.commit()

        instances = OrderableCheckingModel.apply_default_sort().all()
        self.assertEqual(instances[0].order, 0)
        self.assertEqual(instances[2].order, 2)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
