import unittest

from sqlalchemy import Unicode
from nanohttp import settings

from restfulpy.orm import DeclarativeBase, DBSession, Field, ModifiedMixin
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication


class ModificationCheckingModel(ModifiedMixin, DeclarativeBase):
    __tablename__ = 'modification_checking_model'

    title = Field(Unicode(50), primary_key=True)


class ModificationCheckingModelTestCase(WebAppTestCase):
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

    def test_modified_mixin(self):

        # noinspection PyArgumentList
        instance = ModificationCheckingModel(
            title='test title',
        )

        DBSession.add(instance)
        DBSession.commit()
        self.assertIsNone(instance.modified_at)
        self.assertIsNotNone(instance.created_at)
        self.assertEqual(instance.last_modification_time, instance.created_at)

        instance = DBSession.query(ModificationCheckingModel).one()
        self.assertIsNone(instance.modified_at)
        self.assertIsNotNone(instance.created_at)
        self.assertEqual(instance.last_modification_time, instance.created_at)

        instance.title = 'Edited title'
        DBSession.commit()
        self.assertIsNotNone(instance.modified_at)
        self.assertIsNotNone(instance.created_at)
        self.assertEqual(instance.last_modification_time, instance.modified_at)

        instance = DBSession.query(ModificationCheckingModel).one()
        self.assertIsNotNone(instance.modified_at)
        self.assertIsNotNone(instance.created_at)
        self.assertEqual(instance.last_modification_time, instance.modified_at)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
