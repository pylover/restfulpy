from datetime import datetime

import pytest
from bddrest import response, when, status
from dateutil.tz import tzoffset
from nanohttp import json
from sqlalchemy import Integer, DateTime

from restfulpy.configuration import settings
from restfulpy.controllers import JsonPatchControllerMixin, ModelRestController
from restfulpy.datetimehelpers import parse_datetime, format_datetime
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

    def test_timezone_aware_datetime_formatting(self):
        # The application is configured to use a specific timezone as the
        # default
        settings.timezone = tzoffset('Tehran', 12600)

        with pytest.raises(ValueError):
            format_datetime(datetime(1970, 1, 1))

        assert '1970-01-01T00:00:00+03:30' == \
            format_datetime(datetime(1970, 1, 1, tzinfo=tzoffset(None, 12600)))

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

        assert datetime(
            1970, 1, 1, 3, 30, 1, 334300, tzinfo=tzoffset('Tehran', 12600)
        ) == parse_datetime('1.3343')

