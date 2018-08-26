from bddrest import response, when, Update, status
from nanohttp import json
from sqlalchemy import Unicode, Integer, Date, Float, ForeignKey, Boolean, \
    DateTime
from sqlalchemy.ext.associationproxy import association_proxy

from restfulpy.controllers import JsonPatchControllerMixin, ModelRestController
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession, \
    composite, FilteringMixin, PaginationMixin, OrderingMixin, relationship, \
    ModifiedMixin, ActivationMixin, synonym
from restfulpy.testing import ApplicableTestCase


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


class Book(DeclarativeBase):
    __tablename__ = 'book'
    id = Field(Integer, primary_key=True)
    title = Field(Unicode(10), nullable=True)
    member_id = Field(Integer, ForeignKey("member.id"))


class Keyword(DeclarativeBase):
    __tablename__ = 'keyword'
    id = Field(Integer, primary_key=True)
    keyword = Field(Unicode(64))


class MemberKeywords(DeclarativeBase):
    __tablename__ = 'member_keywords'
    member_id = Field(Integer, ForeignKey("member.id"), primary_key=True)
    keyword_id = Field(Integer, ForeignKey("keyword.id"), primary_key=True)


class Member(
    ActivationMixin,
    ModifiedMixin,
    FilteringMixin,
    PaginationMixin,
    OrderingMixin,
    DeclarativeBase
):
    __tablename__ = 'member'

    id = Field(Integer, primary_key=True)
    email = Field(
        Unicode(100),
        unique=True,
        index=True,
        json='email',
        pattern=r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)',
        watermark='Email',
        example="user@example.com",
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
        pattern= \
            r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??'
            r'\d{4}|\d{3}[-\.\s]??\d{4}',
        watermark='Phone'
    )
    name = composite(
        FullName,
        first_name,
        last_name,
        readonly=True,
        json='fullName'
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
    weight = Field(Float(asdecimal=True), default=50)
    _keywords = relationship(
        'Keyword',
        secondary='member_keywords',
        protected=False
    )
    keywords = association_proxy(
        '_keywords',
        'keyword',
        creator=lambda k: Keyword(keyword=k)
    )
    visible = Field(Boolean, nullable=True)
    last_login_time = Field(DateTime, json='lastLoginTime')
    books = relationship('Book', protected=False)

    def _set_password(self, password):
        self._password = 'hashed:%s' % password

    def _get_password(self):  # pragma: no cover
        return self._password

    password = synonym(
        '_password',
        descriptor=property(_get_password, _set_password),
        protected=True
    )

    _avatar = Field('avatar', Unicode(255), nullable=True, protected=True)
    def _set_avatar(self, avatar):  # pragma: no cover
        self._avatar = 'avatar:%s' % avatar

    def _get_avatar(self):  # pragma: no cover
        return self._avatar

    avatar = synonym(
        '_avatar',
        descriptor=property(_get_avatar, _set_avatar),
        protected=False,
        json='avatarImage'
    )


class Root(JsonPatchControllerMixin, ModelRestController):
    __model__ = Member

    @json
    @commit
    def post(self):
        m = Member()
        m.keywords.append('Hello')
        m.update_from_request()
        DBSession.add(m)
        return m

    @json
    @Member.expose
    def get(self, title: str=None):
        query = DBSession.query(Member)
        if title:
            return query.filter(Member.title == title).one_or_none()
        return query

    @json
    @Member.expose
    def me(self):
        return dict(
            title='me'
        )


class TestBaseModel(ApplicableTestCase):
    __controller_factory__ = Root

    def test_update_from_request(self):
        with self.given(
                'Posting a form',
                verb='POST',
                form=dict(
                    title='test',
                    firstName='test',
                    lastName='test',
                    email='test@example.com',
                    password='123456',
                    birth='2001-01-01',
                    weight=1.1,
                    visible='false',
                    lastLoginTime='2017-10-10T15:44:30.000',
                    isActive=True
                )):
            assert response.json['title'] == 'test'
            assert 'avatar' not in response.json
            assert '_avatar' not in response.json
            assert 'avatarImage' in response.json

            # 400 for sending relationship attribute
            when(
                'Sending a relationship attribute',
                form=Update(email='test2@example.com', books=[])
            )
            assert status == '200 OK'
            assert {
                'Keywords': [{'id': 2, 'keyword': 'Hello'}],
                'birth': '2001-01-01',
                'books': [],
                'email': 'test2@example.com',
                'firstName': 'test',
                'fullName': 'test test',
                'id': 2,
                'lastName': 'test',
                'title': 'test',
                'weight': '1.1000000000'
            }.items() <= response.json.items()

    def test_pagination(self):
        with self.given(
                'Getting a single object using pagination',
                query=dict(take=1)
            ):

            assert len(response.json) == 1
            assert response.json[0]['title'] == 'test'
            assert response.json[0]['visible'] == False

            when(
                'Trying to get an non-existence db object',
                '/non-existence-user'
            )
            assert status == 404

            when('Getting a plain dictionary', '/me')
            assert response.json == {'title': 'me'}

    def test_iter_columns(self):
        columns = {
            c.key: c for c in Member.iter_columns(
                relationships=False,
                synonyms=False,
                composites=False
            )
        }
        assert len(columns) == 16
        assert 'name' not in columns
        assert 'password' not in columns
        assert '_password' in columns

    def test_iter_json_columns(self):
        columns = {
            c.key: c for c in Member.iter_json_columns(
                include_readonly_columns=False,
                include_protected_columns=False
            )
        }
        assert len(columns) == 12
        assert 'name' not in columns
        assert 'password' not in columns
        assert '_password' not in columns
        assert '_avatar' not in columns
        assert 'avatar' in columns

    def test_metadata(self):
        with self.given(
            'Fetching the metadata',
            verb='METADATA'
        ):
            assert 'fields' in response.json
            assert 'name' in response.json
            assert 'primaryKeys' in response.json
            assert 'id' in response.json['primaryKeys']
            assert response.json['name'] == 'Member'

            fields = response.json['fields']
            assert 'id' in fields
            assert 'firstName' in fields
            assert fields['id']['primaryKey'] == True
            assert fields['email']['primaryKey'] == False
            assert fields['title']['primaryKey'] == False
            assert fields['title']['minLength'] == 2
            assert fields['title']['maxLength'] == 50
            assert fields['email']['pattern'] == \
                '(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'

            assert fields['firstName']['name'] == 'firstName'
            assert fields['firstName']['key'] == 'first_name'
            assert fields['weight']['default'] == 50
            assert fields['visible']['not_none'] == None
            assert fields['email']['watermark'] == 'Email'
            assert fields['email']['label'] == 'Email'
            assert fields['email']['example'] == 'user@example.com'

