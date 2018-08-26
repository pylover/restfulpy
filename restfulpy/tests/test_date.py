from datetime import date

import pytest
from bddrest import response, when, status
from dateutil.tz import tzoffset
from nanohttp import json
from sqlalchemy import Integer, Date

from restfulpy.configuration import settings
from restfulpy.controllers import JsonPatchControllerMixin, ModelRestController
from restfulpy.datetimehelpers import parse_datetime, format_datetime, \
    parse_date, format_date
from restfulpy.mockup import mockup_localtimezone
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession
from restfulpy.testing import ApplicableTestCase


class Party(DeclarativeBase):
    __tablename__ = 'party'
    id = Field(Integer, primary_key=True)
    when = Field(Date)


class Root(JsonPatchControllerMixin, ModelRestController):
    __model__ = 'party'

    @json
    @commit
    def post(self):
        m = Party()
        m.update_from_request()
        DBSession.add(m)
        return m.when.isoformat()


class TestDate(ApplicableTestCase):
    __controller_factory__ = Root

    def test_update_from_request(self):
        with self.given(
            'Posting a date in form',
            verb='POST',
            form=dict(
                when='2001-01-01',
            )
        ):
            assert status == 200
            assert response.json == '2001-01-01'

            when(
                'Posix time format',
                form=dict(
                    when='1513434403'
                )
            )
            assert status == 200
            assert response.json == '2017-12-16'

            when(
                'Posting a datetime instead of date',
                form=dict(
                    when='2001-01-01T00:01:00.123456'
                )
            )
            assert status == 200
            assert response.json == '2001-01-01'

            when(
                'Posting an invalid datetime',
                form=dict(
                    when='2001-00-01'
                )
            )
            assert status == '400 Invalid date or time: 2001-00-01'

    def test_date_parsing(self):
        assert date(1970, 1, 1) == parse_date('1970-01-01')
        assert date(1970, 1, 1) == parse_date('1970-01-01T00:00:00.001')
        assert date(1970, 1, 1) == parse_date('1970-01-01T00:00:00.001000')

    def test_date_formatting(self):
        assert '1970-01-01' == format_date(date(1970, 1, 1))

    def test_unix_timestamp(self):
        assert date(1970, 1, 1) == parse_date('1.3343')

