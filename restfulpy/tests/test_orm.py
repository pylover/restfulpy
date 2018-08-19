from datetime import date, time

import pytest
from nanohttp import HTTPBadRequest, settings
from nanohttp.contexts import Context
from sqlalchemy import Integer, Unicode, ForeignKey, Boolean, Table, Date,\
    Time, Float
from sqlalchemy.orm import synonym

from restfulpy.orm import DeclarativeBase, Field, relationship, composite, \
    ModifiedMixin


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
    email = Field(
        Unicode(100),
        unique=True,
        index=True,
        json='email',
        pattern=r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)',
        watermark='Email',
        example="user@example.com"
    )
    title = Field(
        Unicode(50),
        index=True,
        min_length=2,
        watermark='First Name'
    )
    first_name = Field(
        Unicode(50),
        index=True,
        json='firstName',
        min_length=2,
        watermark='First Name'
    )
    last_name = Field(
        Unicode(100),
        json='lastName',
        min_length=2,
        watermark='Last Name'
    )
    phone = Field(
        Unicode(10), nullable=True, json='phone', min_length=10,
        pattern=\
            r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??'
            r'\d{4}|\d{3}[-\.\s]??\d{4}',
        watermark='Phone'
    )
    name = composite(
        FullName,
        first_name,
        last_name,
        readonly=True,
        json='fullName',
        protected=True
    )
    _password = Field(
        'password',
        Unicode(128),
        index=True,
        json='password',
        protected=True,
        min_length=6
    )
    birth = Field(Date)
    weight = Field(Float(asdecimal=True))
    age = Field(Integer, default=18, minimum=18, maximum=100)

    def _set_password(self, password):
        self._password = 'hashed:%s' % password

    def _get_password(self):  # pragma: no cover
        return self._password

    password = synonym(
        '_password',
        descriptor=property(_get_password, _set_password),
        info=dict(protected=True)
    )


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


post_tag_table = Table(
    'post_tag', DeclarativeBase.metadata,
    Field('post_id', Integer, ForeignKey('post.id')),
    Field('tag_id', Integer, ForeignKey('tag.id'))
)


class Tag(DeclarativeBase):
    __tablename__ = 'tag'
    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50), watermark='title', label='title')
    posts = relationship(
        'Post',
        secondary=post_tag_table,
        back_populates='tags'
    )


class Post(ModifiedMixin, DeclarativeBase):
    __tablename__ = 'post'

    id = Field(Integer, primary_key=True)
    title = Field(Unicode(50), watermark='title', label='title')
    author_id = Field(ForeignKey('author.id'), json='authorId')
    author = relationship(Author, protected=False)
    memos = relationship(Memo, protected=True, json='privateMemos')
    comments = relationship(Comment, protected=False)
    tags = relationship(
        Tag,
        secondary=post_tag_table,
        back_populates='posts',
        protected=False
    )
    tag_time = Field(Time)


def test_model(db):
    session = db()

    __configuration__ = '''
    timezone:
    '''

    settings.merge(__configuration__)

    with Context({}):
        author1 = Author(
            title='author1',
            email='author1@example.org',
            first_name='author 1 first name',
            last_name='author 1 last name',
            phone=None,
            password='123456',
            birth=date(1, 1, 1),
            weight=1.1
        )

        post1 = Post(
            title='First post',
            author=author1,
            tag_time=time(1, 1, 1)
        )
        session.add(post1)
        session.commit()

        assert post1.id == 1

        post1_dict = post1.to_dict()
        assert {
                'author': {
                    'email': 'author1@example.org',
                    'firstName': 'author 1 first name',
                    'id': 1,
                    'lastName': 'author 1 last name',
                    'phone': None,
                    'title': 'author1',
                    'birth': '0001-01-01',
                    'weight': 1.100,
                    'age': 18
                },
                'authorId': 1,
                'comments': [],
                'id': 1,
                'tags': [],
                'title': 'First post',
                'tagTime': '01:01:01',
            }.items() < post1_dict.items()

        assert 'createdAt' in post1_dict
        assert 'modifiedAt' in post1_dict

        author1_dict = author1.to_dict()
        assert 'fullName' not in author1_dict


def test_metadata(db):
        # Metadata
        author_metadata = Author.json_metadata()
        assert 'id' in author_metadata['fields']
        assert'email' in author_metadata['fields']
        assert author_metadata['fields']['fullName']['protected'] == True
        assert author_metadata['fields']['password']['protected'] == True

        post_metadata = Post.json_metadata()
        assert'author' in post_metadata['fields']

        comment_metadata = Comment.json_metadata()
        assert 'post' in comment_metadata['fields']

        tag_metadata = Tag.json_metadata()
        assert 'posts' in tag_metadata['fields']

        assert Comment.import_value(Comment.__table__.c.special, 'TRUE') ==\
            True

