from bddrest import response, status, when
from nanohttp import json
from sqlalchemy import Unicode, Integer

from restfulpy.controllers import ModelRestController
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession
from restfulpy.testing import ApplicableTestCase


class Supervisor(DeclarativeBase):
    __tablename__ = 'supervisor'

    id = Field(
        Integer,
        primary_key=True,
        readonly='709 id is readonly'
    )
    email = Field(
        Unicode(100),
        not_none='701 email cannot be null',
        required='702 email required',
        pattern=(
            '(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)',
            '707 Invalid email address'
        ),
        watermark='Email',
        example="user@example.com"
    )
    title = Field(
        Unicode(50),
        index=True,
        min_length=(4, '703 title must be at least 4 characters'),
        max_length=(50, '704 Maximum allowed length for title is 50'),
        watermark='First Name',
        nullable=True,
    )
    age = Field(
        Integer,
        nullable=True,
        python_type=(int, '705 age must be integer'),
        minimum=(18, '706 age must be greater than 17'),
        maximum=(99, '706 age must be less than 100')
    )


class Root(ModelRestController):
    __model__ = Supervisor

    @json
    @commit
    @Supervisor.validate(strict=True)
    @Supervisor.expose
    def post(self):
        m = Supervisor()
        m.update_from_request()
        DBSession.add(m)
        return m

    @json
    @commit
    @Supervisor.validate
    @Supervisor.expose
    def put(self):
        m = Supervisor()
        m.update_from_request()
        DBSession.add(m)
        return m


    @json
    @Supervisor.expose
    def get(self):
        return DBSession.query(Supervisor).first()


class TestModelValidationDecorator(ApplicableTestCase):
    __controller_factory__ = Root

    def test_string_codec(self):
        with self.given(
            'Whitebox',
            verb='POST',
            form=dict(
                title='white',
                email='user@example.com',
            ),
        ):
            assert status == 200
            assert response.json['title'] == 'white'

            when(
                'Not strict',
                verb='PUT',
                form=dict(
                    email='userput@example.com'
                )
            )
            assert status == 200


            when(
                'Invalid email format',
                form=dict(
                    title='black1',
                    email='inavlidformat'
                )
            )
            assert status == 707

            when(
                'Passing readonly field',
                form=dict(
                    id=22,
                    title='black2',
                    email='user@example.com'
                )
            )
            assert status == 709

