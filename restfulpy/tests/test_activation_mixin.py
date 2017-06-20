import unittest

from sqlalchemy import Integer, Unicode
from nanohttp import configure

from restfulpy.orm import DeclarativeBase, init_model, create_engine, Field, DBSession, setup_schema, ActivationMixin


class ActiveObject(ActivationMixin, DeclarativeBase):
    __tablename__ = 'active_object'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50), index=True, min_length=2, watermark='First Name')


class ActivationMixinTestCase(unittest.TestCase):
    __configuration__ = '''
    db:
      uri: sqlite://    # In memory DB
      echo: false
    '''

    @classmethod
    def setUpClass(cls):
        configure(init_value=cls.__configuration__, force=True)
        cls.engine = create_engine()
        init_model(cls.engine)
        setup_schema()

    def test_model(self):
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
