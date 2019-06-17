from datetime import datetime, timedelta, time, date

import pytest
from bddrest import response, when, status
from dateutil.tz import tzoffset, tzstr
from nanohttp import json
from sqlalchemy import Integer, DateTime

from freezegun import freeze_time
from restfulpy.configuration import settings
from restfulpy.controllers import JsonPatchControllerMixin, ModelRestController
from restfulpy.datetimehelpers import parse_datetime, format_datetime, \
    localnow, parse_time, localtimezone
from restfulpy.mockup import mockup_localtimezone
from restfulpy.orm import commit, DeclarativeBase, Field, DBSession
from restfulpy.testing import ApplicableTestCase


class Metting(DeclarativeBase):
    __tablename__ = 'metting'
    id = Field(Integer, primary_key=True)
    when = Field(DateTime)


class Root(JsonPatchControllerMixin, ModelRestController):
    __model__ = 'metting'

    @json
    @commit
    def post(self):
        m = Metting()
        m.update_from_request()
        DBSession.add(m)
        return m.when.isoformat()


class TestDateTime(ApplicableTestCase):
    __controller_factory__ = Root

    def test_update_from_request(self):
        with self.given(
            'Posting a datetime in form',
            verb='POST',
            form=dict(
                when='2001-01-01T00:01',
            )
        ):
            assert status == 200
            assert response.json == '2001-01-01T00:01:00'

            when(
                'Posting a date instead of datetime',
                form=dict(
                    when='2001-01-01'
                )
            )

            assert status == 200
            assert response.json == '2001-01-01T00:00:00'

            when(
                'Posting an invalid datetime',
                form=dict(
                    when='2001-00-01'
                )
            )

            assert status == '400 Invalid date or time: 2001-00-01'

    def test_naive_datetime_parsing(self):
        # The application is configured to use system's local date and time.
        settings.timezone = None

        # Submit without timezone: accept and assume the local date and time.
        assert datetime(1970, 1, 1) == parse_datetime('1970-01-01')
        assert datetime(1970, 1, 1) == parse_datetime('1970-01-01T00:00:00')
        assert datetime(1970, 1, 1, microsecond=1000) == \
            parse_datetime('1970-01-01T00:00:00.001')
        assert datetime(1970, 1, 1, microsecond=1000) == \
            parse_datetime('1970-01-01T00:00:00.001000')

        # Timezone aware
        # Submit with 'Z' and or '+3:30':
        # accept and assume as the UTC, so we have to convert
        # it to local date and time before continuing the rest of process
        with mockup_localtimezone(tzoffset(None, 3600)):
            assert datetime(1970, 1, 1, 1) == \
                parse_datetime('1970-01-01T00:00:00Z')
            assert datetime(1970, 1, 1, 1, 30) == \
                parse_datetime('1970-01-01T00:00:00-0:30')

    def test_timezone_aware_datetime_parsing(self):
        # The application is configured to use a specific timezone
        settings.timezone = tzoffset('Tehran', 12600)
        with pytest.raises(ValueError):
            parse_datetime('1970-01-01T00:00:00')

        assert datetime(1970, 1, 1, 3, 30, tzinfo=tzoffset(
            'Tehran', 12600)) == parse_datetime('1970-01-01T00:00:00Z')
        assert datetime(1970, 1, 1, 4, 30, tzinfo=tzoffset(
            'Tehran', 12600)) == parse_datetime('1970-01-01T00:00:00-1:00')

    def test_naive_datetime_formatting(self):
        # The application is configured to use system's local date and time.
        settings.timezone = None

        assert '1970-01-01T00:00:00' == format_datetime(datetime(1970, 1, 1))
        assert '1970-01-01T00:00:00.000001' == \
            format_datetime(datetime(1970, 1, 1, 0, 0, 0, 1))

        with mockup_localtimezone(tzoffset(None, 3600)):
            assert '1970-01-01T00:00:00' == format_datetime(
                datetime(1970, 1, 1, tzinfo=tzoffset(None, 3600))
            )

        assert '1970-01-01T00:00:00' == format_datetime(date(1970, 1, 1))

    def test_timezone_aware_datetime_formatting(self):
        # The application is configured to use a specific timezone as the
        # default
        settings.timezone = tzoffset('Tehran', 12600)

        with pytest.raises(ValueError):
            format_datetime(datetime(1970, 1, 1))

        assert '1970-01-01T00:00:00+03:30' == \
            format_datetime(datetime(1970, 1, 1, tzinfo=tzoffset(None, 12600)))

        assert '1970-01-01T00:00:00+03:30' == format_datetime(date(1970, 1, 1))

    def test_different_timezone_formatting(self):
        settings.timezone = tzoffset('Tehran', 12600)
        assert '1970-01-01T06:31:00+03:30' == \
            format_datetime(datetime(1970, 1, 1, 1, 1, tzinfo=tzstr('GMT-2')))

    def test_naive_unix_timestamp(self):
        # The application is configured to use system's local date and time.
        settings.timezone = None

        assert datetime(1970,1,1,0,0,1,334300) == \
            parse_datetime('1.3343')
        assert datetime(1970,1,1,0,0,1,334300) == \
            parse_datetime('1.3343')

    def test_timezone_aware_unix_timestamp(self):
        # The application is configured to use a specific timezone as the
        # default
        settings.timezone = tzoffset('Tehran', 12600)
        dt = parse_datetime('1.3343')
        assert dt == datetime(
            1970, 1, 1, 3, 30, 1, 334300, tzinfo=tzoffset('Tehran', 12600)
        )
        assert dt.utcoffset() == timedelta(0, 12600)

    def test_timezone_named(self):
        # The application is configured to use a named timzone
        settings.timezone = 'utc'
        dt = parse_datetime('1.3343')
        assert dt == datetime(
            1970, 1, 1, 3, 30, 1, 334300, tzinfo=tzoffset('Tehran', 12600)
        )
        assert dt.utcoffset() == timedelta(0)

    def test_timezone_string(self):
        # The application is configured to use a named timzone
        settings.timezone = 'GMT+3'
        dt = parse_datetime('1.3343')
        assert dt == datetime(
            1970, 1, 1, 3, 30, 1, 334300, tzinfo=tzoffset('Tehran', 12600)
        )
        assert dt.utcoffset() == timedelta(0, 10800)

    def test_local_datetime(self):
        # The application is configured to use a named timzone
        settings.timezone = 'GMT+3'
        with freeze_time('2000-01-01T01:01:00'):
            now = localnow()
            assert now == datetime(2000, 1, 1, 4, 1, tzinfo=tzstr('GMT+3'))
            assert now.utcoffset() == timedelta(0, 10800)

    def test_parse_time_posix_timestamp(self):
        assert parse_time(1000000.11) == time(13, 46, 40, 110000)
        assert parse_time('1000000.11') == time(13, 46, 40, 110000)

    def test_localtimezone(self):
        assert localtimezone() is not None

