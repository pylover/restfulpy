import unittest
from datetime import date, datetime

from nanohttp import json, settings, context
from sqlalchemy import Unicode, Integer, Date, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import synonym
from sqlalchemy.ext.associationproxy import association_proxy

from restfulpy.controllers import JsonPatchControllerMixin, ModelRestController
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession, composite, FilteringMixin, PaginationMixin, \
    OrderingMixin, relationship, ModifiedMixin, ActivationMixin
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication


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


class Member(ActivationMixin, ModifiedMixin, FilteringMixin, PaginationMixin, OrderingMixin, DeclarativeBase):
    __tablename__ = 'member'

    id = Field(Integer, primary_key=True)
    email = Field(Unicode(100), unique=True, index=True, json='email',
                  pattern=r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', watermark='Email',
                  example="user@example.com", message='Invalid email address, please be accurate!', icon='email.svg')
    title = Field(Unicode(50), index=True, min_length=2, watermark='First Name')
    first_name = Field(Unicode(50), index=True, json='firstName', min_length=2, watermark='First Name')
    last_name = Field(Unicode(100), json='lastName', min_length=2, watermark='Last Name')
    phone = Field(
        Unicode(10), nullable=True, json='phone', min_length=10,
        pattern=r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}',
        watermark='Phone'
    )
    name = composite(FullName, first_name, last_name, readonly=True, json='fullName')
    _password = Field('password', Unicode(128), index=True, json='password', protected=True, min_length=6)
    birth = Field(Date)
    weight = Field(Float(asdecimal=True), default=50)
    _keywords = relationship('Keyword', secondary='member_keywords')
    keywords = association_proxy('_keywords', 'keyword', creator=lambda k: Keyword(keyword=k))
    visible = Field(Boolean, nullable=True)
    last_login_time = Field(DateTime, json='lastLoginTime')
    books = relationship('Book')

    def _set_password(self, password):
        self._password = 'hashed:%s' % password

    def _get_password(self):  # pragma: no cover
        return self._password

    password = synonym('_password', descriptor=property(_get_password, _set_password), info=dict(protected=True))


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
        query = Member.query
        if title:
            return query.filter(Member.title == title).one_or_none()
        return query

    @json
    @Member.expose
    def me(self):
        return dict(
            title='me'
        )


class BaseModelTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', Root())
    __configuration__ = '''
    db:
      url: sqlite://    # In memory DB
      echo: false
    '''

    @classmethod
    def configure_app(cls):
        cls.application.configure(force=True)
        settings.merge(cls.__configuration__)
        settings.merge('''
        logging:
          loggers:
            default:
              level: debug
        ''')

    def test_update_from_request(self):
        resp, ___ = self.request(
            'ALL', 'POST', '/', params=dict(
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
            ),
            doc=False
        )
        self.assertEqual(resp['title'], 'test')

        resp, ___ = self.request('ALL', 'GET', '/', query_string=dict(take=1), doc=False)
        self.assertEqual(len(resp), 1)
        self.assertEqual(resp[0]['title'], 'test')
        self.assertEqual(resp[0]['visible'], False)

        # 404
        self.request('ALL', 'GET', '/non-existence-user', doc=False, expected_status=404)

        # Plain dictionary
        resp, ___ = self.request('ALL', 'GET', '/me', doc=False)
        self.assertEqual(resp['title'], 'me')

        # 400 for sending relationship attribute
        self.request(
            'ALL', 'POST', '/', json=dict(
                title='test',
                firstName='test',
                lastName='test',
                email='test@example.com',
                password='123456',
                birth='2001-01-01',
                weight=1.1,
                visible='false',
                lastLoginTime='2017-10-10T15:44:30.000',
                isActive=True,
                books=[]
            ),
            doc=False,
            expected_status=400
        )

    def test_iter_columns(self):
        columns = {c.key: c for c in Member.iter_columns(relationships=False, synonyms=False, composites=False)}
        self.assertEqual(len(columns), 15)
        self.assertNotIn('name', columns)
        self.assertNotIn('password', columns)
        self.assertIn('_password', columns)

    def test_iter_json_columns(self):
        columns = {c.key: c for c in Member.iter_json_columns(
            include_readonly_columns=False, include_protected_columns=False)}
        self.assertEqual(len(columns), 13)
        self.assertNotIn('name', columns)
        self.assertNotIn('password', columns)
        self.assertNotIn('_password', columns)

    def test_metadata(self):
        resp, ___ = self.request('ALL', 'METADATA', '/', doc=False)

        self.assertIn('fields', resp)
        self.assertIn('name', resp)
        self.assertIn('primaryKeys', resp)
        self.assertIn('id', resp['primaryKeys'])
        self.assertEqual(resp['name'], 'Member')
        fields = resp['fields']
        self.assertIn('id', fields)
        self.assertIn('firstName', fields)
        self.assertEqual(fields['id']['primaryKey'], True)
        self.assertEqual(fields['email']['primaryKey'], False)
        self.assertEqual(fields['title']['primaryKey'], False)
        self.assertEqual(fields['title']['minLength'], 2)
        self.assertEqual(fields['title']['maxLength'], 50)
        self.assertEqual(fields['email']['pattern'], '(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')

        self.assertEqual(fields['firstName']['name'], 'firstName')
        self.assertEqual(fields['firstName']['key'], 'first_name')

        self.assertEqual(fields['firstName']['type_'], 'str')
        self.assertEqual(fields['birth']['type_'], 'date')

        self.assertEqual(fields['weight']['default_'], 50)
        self.assertEqual(fields['visible']['optional'], True)

        self.assertEqual(fields['email']['message'], 'Invalid email address, please be accurate!')
        self.assertEqual(fields['email']['watermark'], 'Email')
        self.assertEqual(fields['email']['label'], 'Email')
        self.assertEqual(fields['email']['icon'], 'email.svg')
        self.assertEqual(fields['email']['example'], 'user@example.com')

    def test_datetime_format(self):
        # datetime allows contain microseconds
        self.request(
            'ALL', 'POST', '/',
            params=dict(
                title='test',
                firstName='test',
                lastName='test',
                email='test1@example.com',
                password='123456',
                birth='2001-01-01',
                weight=1.1,
                visible='false',
                lastLoginTime='2017-10-10T10:10:00.12313'
            ),
            doc=False
        )
        self.request(
            'ALL', 'POST', '/',
            params=dict(
                title='test',
                firstName='test',
                lastName='test',
                email='test2@example.com',
                password='123456',
                birth='2001-01-01',
                weight=1.1,
                visible='false',
                lastLoginTime='2017-10-10T10:10:00.'
            ),
            doc=False,
            expected_status=400
        )

        self.request(
            'ALL', 'POST', '/',
            params=dict(
                title='test',
                firstName='test',
                lastName='test',
                email='test3@example.com',
                password='123456',
                birth='2001-01-01',
                weight=1.1,
                visible='false',
                lastLoginTime='2017-10-10T10:10:00'
            ),
            doc=False
        )

        # Invalid month value
        self.request(
            'ALL', 'POST', '/',
            params=dict(
                title='test',
                firstName='test',
                lastName='test',
                email='test4@example.com',
                password='123456',
                birth='2001-01-01',
                weight=1.1,
                visible='false',
                lastLoginTime='2017-13-10T10:10:00'
            ),
            doc=False,
            expected_status=400
        )

        # Invalid datetime format
        self.request(
            'ALL', 'POST', '/',
            params=dict(
                title='test',
                firstName='test',
                lastName='test',
                email='test4@example.com',
                password='123456',
                birth='2001-01-01',
                weight=1.1,
                visible='false',
                lastLoginTime='InvalidDatetime'
            ),
            doc=False,
            expected_status=400
        )

        # datetime might not have ending Z
        resp, ___ = self.request(
            'ALL', 'POST', '/',
            params=dict(
                title='test',
                firstName='test',
                lastName='test',
                email='test5@example.com',
                password='123456',
                birth='2001-01-01',
                weight=1.1,
                visible='false',
                lastLoginTime='2017-10-10T10:10:00.4546'
            ),
            doc=False
        )
        self.assertEqual(resp['lastLoginTime'], '2017-10-10T10:10:00.004546Z')

        # datetime containing ending Z
        resp, ___ = self.request(
            'ALL', 'POST', '/', params=dict(
                title='test',
                firstName='test',
                lastName='test',
                email='test6@example.com',
                password='123456',
                birth='2001-01-01',
                weight=1.1,
                visible='false',
                lastLoginTime='2017-10-10T10:10:00.4546Z'
            ),
            doc=False
        )
        self.assertEqual(resp['lastLoginTime'], '2017-10-10T10:10:00.004546Z')

    def test_date_format(self):
        # iso date format
        resp, ___ = self.request(
            'ALL', 'POST', '/',
            params=dict(
                title='test',
                firstName='test',
                lastName='test',
                email='test11@example.com',
                password='123456',
                birth='2001-01-01',
                weight=1.1,
                visible='false',
                lastLoginTime='2017-10-10T10:10:00.4546Z'
            ),
            doc=False
        )
        self.assertEqual(resp['birth'], '2001-01-01')
        self.assertEqual(resp['lastLoginTime'], '2017-10-10T10:10:00.004546Z')

        # posix timestamp
        resp, ___ = self.request(
            'ALL', 'POST', '/',
            params=dict(
                title='test',
                firstName='test',
                lastName='test',
                email='test12@example.com',
                password='123456',
                birth='1513434403',
                weight=1.1,
                visible='false',
                lastLoginTime=datetime(2017, 10, 10, 10, 10, 0, 4546).timestamp()
            ),
            doc=False
        )
        self.assertEqual(resp['birth'], '2017-12-16')
        self.assertEqual(resp['lastLoginTime'], '2017-10-10T10:10:00.004546Z')

        # none iso date format
        self.request(
            'ALL', 'POST', '/',
            params=dict(
                title='test',
                firstName='test',
                lastName='test',
                email='test13@example.com',
                password='123456',
                birth='01-01-01',
                weight=1.1,
                visible='false',
                lastLoginTime='2017-10-10T10:10:00.4546Z'
            ),
            doc=False,
            expected_status=400
        )

        # none iso date format
        self.request(
            'ALL', 'POST', '/',
            params=dict(
                title='test',
                firstName='test',
                lastName='test',
                email='test14@example.com',
                password='123456',
                birth='2001/01/01',
                weight=1.1,
                visible='false',
                lastLoginTime='2017-10-10T10:10:00.4546Z'
            ),
            doc=False,
            expected_status=400
        )


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
