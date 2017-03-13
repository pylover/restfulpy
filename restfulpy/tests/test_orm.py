import unittest

from sqlalchemy import Integer, Unicode, ForeignKey, Boolean
from sqlalchemy.orm import synonym
from nanohttp import configure, HttpBadRequest

from restfulpy.orm import DeclarativeBase, init_model, create_engine, Field, DBSession, setup_schema, relationship, \
    composite


class FullName(object):  # pragma: no cover
    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name

    def __composite_values__(self):
        return '%s %s' % (self.first_name, self.last_name)

    def __repr__(self):
        return "FullName(%s %s)" % (self.first_name, self.last_name)

    def __eq__(self, other):
        return isinstance(other, FullName) and \
               other.first_name == self.first_name and \
               other.last_name == self.last_name

    def __ne__(self, other):
        return not self.__eq__(other)


class Author(DeclarativeBase):
    __tablename__ = 'author'

    id = Field(Integer, primary_key=True)
    email = Field(Unicode(100), unique=True, index=True, json='email',
                  pattern=r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', watermark='Email',
                  example="user@example.com")
    title = Field(Unicode(50), index=True, min_length=2, watermark='First Name')
    first_name = Field(Unicode(50), index=True, json='firstName', min_length=2, watermark='First Name')
    last_name = Field(Unicode(100), json='lastName', min_length=2, watermark='Last Name')
    phone = Field(
        Unicode(10), nullable=True, json='phone', min_length=10,
        pattern=r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}',
        watermark='Phone'
    )
    name = composite(FullName, first_name, last_name, readonly=True, json='fullName', protected=True)
    _password = Field('password', Unicode(128), index=True, json='password', protected=True, min_length=6)

    def _set_password(self, password):
        self._password = 'hashed:%s' % password

    def _get_password(self):
        return self._password

    password = synonym('_password', descriptor=property(_get_password, _set_password), info=dict(protected=True))


class Memo(DeclarativeBase):
    __tablename__ = 'memo'
    id = Field(Integer, primary_key=True)
    content = Field(Unicode(100), max_length=90)
    post_id = Field(ForeignKey('post.id'), json='postId')


class Comment(DeclarativeBase):
    __tablename__ = 'comment'
    id = Field(Integer, primary_key=True)
    content = Field(Unicode(100), max_length=90)
    special = Field(Boolean, default=True)
    post_id = Field(ForeignKey('post.id'), json='postId')
    post = relationship('Post')


class Post(DeclarativeBase):
    __tablename__ = 'post'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50), watermark='title', label='title', icon='star')
    author_id = Field(ForeignKey('author.id'), json='authorId')
    author = relationship(Author)
    memos = relationship(Memo, protected=True, json='privateMemos')
    comments = relationship(Comment)


class ModelTestCase(unittest.TestCase):
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

        author1 = Author(
            title='author1',
            email='author1@example.org',
            first_name='author 1 first name',
            last_name='author 1 last name',
            phone=None,
            password='123456'
        )

        post1 = Post(
            title='First post',
            author=author1,
        )
        DBSession.add(post1)
        DBSession.commit()

        self.assertEqual(post1.id, 1)

        # Validation, Type
        with self.assertRaises(HttpBadRequest):
            Author(title=234)

        # Validation, Pattern
        with self.assertRaises(HttpBadRequest):
            Author(email='invalidEmailAddress')

        # Validation, Min length
        with self.assertRaises(HttpBadRequest):
            Author(title='1')

        # Validation, Max length
        with self.assertRaises(HttpBadRequest):
            Author(phone='12321321321312321312312')

        # Metadata
        author_metadata = Author.json_metadata()
        self.assertIn('id', author_metadata)
        self.assertIn('email', author_metadata)
        self.assertNotIn('fullName', author_metadata)
        self.assertNotIn('password', author_metadata)

        post_metadata = Post.json_metadata()
        self.assertIn('author', post_metadata)

        comment_metadata = Comment.json_metadata()
        self.assertIn('post', comment_metadata)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
