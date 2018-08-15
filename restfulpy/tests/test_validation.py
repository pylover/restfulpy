from datetime import date, time

import pytest
from nanohttp import HTTPBadRequest, settings
from nanohttp.contexts import Context
from sqlalchemy import Integer, Unicode, ForeignKey, Boolean, Table, Date,\
    Time, Float
from sqlalchemy.orm import synonym

from restfulpy.orm import DeclarativeBase, Field, relationship, composite, \
    ModifiedMixin


class Actor(DeclarativeBase):
    __tablename__ = 'actor'

    id = Field(Integer, primary_key=True)
    email = Field(
        Unicode(100),
        not_none='701 email cannot be null',
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


def test_validation(db):
    session = db()

    validate = Actor.create_validator()
    values = validate(dict(
        email='user@example.com',
    ))
    assert values['email'] == 'user@example.com'

    with pytest.raises(HTTPStatus) as ctx:
        validate(dict=(email=None))
    assert str(ctx.exception) == ''


