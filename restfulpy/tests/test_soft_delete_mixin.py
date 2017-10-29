import unittest

from sqlalchemy import Unicode
from nanohttp import settings, HttpConflict

from restfulpy.orm import DeclarativeBase, DBSession, Field, SoftDeleteMixin
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication


class SoftDeleteCheckingModel(SoftDeleteMixin, DeclarativeBase):
    __tablename__ = 'soft_delete_checking_model'

    title = Field(Unicode(50), primary_key=True)


class SoftDeleteCheckingModelTestCase(WebAppTestCase):
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

    def test_soft_delete_mixin(self):
        # noinspection PyArgumentList
        instance = SoftDeleteCheckingModel(
            title='test title'
        )
        DBSession.add(instance)
        DBSession.commit()
        instance.assert_is_not_deleted()
        self.assertRaises(ValueError, instance.assert_is_deleted)

        instance = SoftDeleteCheckingModel.query.one()
        instance.soft_delete()
        DBSession.commit()
        instance.assert_is_deleted()
        self.assertRaises(ValueError, instance.assert_is_not_deleted)

        self.assertEqual(SoftDeleteCheckingModel.filter_deleted().count(), 1)
        self.assertEqual(SoftDeleteCheckingModel.exclude_deleted().count(), 0)

        instance.soft_undelete()
        DBSession.commit()
        instance.assert_is_not_deleted()
        self.assertRaises(ValueError, instance.assert_is_deleted)

        self.assertEqual(SoftDeleteCheckingModel.filter_deleted().count(), 0)
        self.assertEqual(SoftDeleteCheckingModel.exclude_deleted().count(), 1)

        DBSession.delete(instance)
        self.assertRaises(HttpConflict, DBSession.commit)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
