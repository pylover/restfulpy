import unittest

from sqlalchemy import Integer, Unicode
from nanohttp import settings

from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.orm import DeclarativeBase, Field, DBSession, DeactivationMixin


class DeactiveObject(DeactivationMixin, DeclarativeBase):
    __tablename__ = 'deactive_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))


class DeactivationMixinTestCase(WebAppTestCase):
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

    def test_deactivation_mixin(self):
        # noinspection PyArgumentList
        object1 = DeactiveObject(
            title='object 1',
        )

        DBSession.add(object1)
        DBSession.commit()

        self.assertFalse(object1.is_active)
        self.assertEqual(DBSession.query(DeactiveObject).filter(DeactiveObject.is_active).count(), 0)

        object1.is_active = True
        self.assertTrue(object1.is_active)
        DBSession.commit()
        object1 = DBSession.query(DeactiveObject).one()
        self.assertTrue(object1.is_active)
        self.assertIsNone(object1.deactivated_at)
        self.assertIsNotNone(object1.activated_at)

        object1.is_active = False
        self.assertFalse(object1.is_active)
        DBSession.commit()
        object1 = DBSession.query(DeactiveObject).one()
        self.assertFalse(object1.is_active)
        self.assertIsNone(object1.activated_at)
        self.assertIsNotNone(object1.deactivated_at)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
