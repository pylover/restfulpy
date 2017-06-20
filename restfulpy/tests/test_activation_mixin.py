import unittest

from sqlalchemy import Integer, Unicode
from nanohttp import settings

from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication
from restfulpy.orm import DeclarativeBase, Field, DBSession, ActivationMixin


class ActiveObject(ActivationMixin, DeclarativeBase):
    __tablename__ = 'active_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50), index=True, min_length=2, watermark='First Name')


class ActivationMixinTestCase(WebAppTestCase):
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

    def test_activation_mixin(self):
        # noinspection PyArgumentList
        object1 = ActiveObject(
            title='object 1',
        )

        DBSession.add(object1)
        DBSession.commit()

        json = object1.to_dict()
        self.assertIn('isActive', json)

        # # Metadata
        # author_metadata = Author.json_metadata()
        # self.assertIn('id', author_metadata)
        # self.assertIn('email', author_metadata)
        # self.assertNotIn('fullName', author_metadata)
        # self.assertNotIn('password', author_metadata)
        #
        # post_metadata = Post.json_metadata()
        # self.assertIn('author', post_metadata)
        #
        # comment_metadata = Comment.json_metadata()
        # self.assertIn('post', comment_metadata)
        #

if __name__ == '__main__':  # pragma: no cover
    unittest.main()
