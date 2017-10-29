import unittest

from sqlalchemy import Integer, Unicode
from nanohttp import settings

from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.orm import DeclarativeBase, Field, DBSession, ApproveRequiredMixin


class ApproveRequiredObject(ApproveRequiredMixin, DeclarativeBase):
    __tablename__ = 'approve_required_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50))


class ApproveRequiredMixinTestCase(WebAppTestCase):
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

    def test_approve_required_mixin(self):
        # noinspection PyArgumentList
        object1 = ApproveRequiredObject(
            title='object 1',
        )

        DBSession.add(object1)
        DBSession.commit()
        self.assertFalse(object1.is_approved)
        self.assertEqual(DBSession.query(ApproveRequiredObject).filter(ApproveRequiredObject.is_approved).count(), 0)

        object1.is_approved = True
        self.assertTrue(object1.is_approved)
        DBSession.commit()
        object1 = DBSession.query(ApproveRequiredObject).one()
        self.assertTrue(object1.is_approved)

        json = object1.to_dict()
        self.assertIn('isApproved', json)

        self.assertEqual(DBSession.query(ApproveRequiredObject).filter(ApproveRequiredObject.is_approved).count(), 1)
        self.assertEqual(ApproveRequiredObject.filter_approved().count(), 1)

        self.assertFalse(ApproveRequiredObject.import_value(ApproveRequiredObject.is_approved, 'false'))
        self.assertFalse(ApproveRequiredObject.import_value(ApproveRequiredObject.is_approved, 'FALSE'))
        self.assertFalse(ApproveRequiredObject.import_value(ApproveRequiredObject.is_approved, 'False'))
        self.assertTrue(ApproveRequiredObject.import_value(ApproveRequiredObject.is_approved, 'true'))
        self.assertTrue(ApproveRequiredObject.import_value(ApproveRequiredObject.is_approved, 'TRUE'))
        self.assertTrue(ApproveRequiredObject.import_value(ApproveRequiredObject.is_approved, 'True'))

        self.assertEqual(ApproveRequiredObject.import_value(ApproveRequiredObject.title, 'title'), 'title')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
