import unittest
from datetime import datetime, timedelta
from dateutil.tz import tzutc, tzoffset
from os.path import dirname, join

from restfulpy.datetimehelpers import parse_datetime, format_datetime
from restfulpy.configuration import configure, settings
from restfulpy.testing import mockup_localtimezone


class DateTimeParserFormatterTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        root_path = dirname(__file__)

        context = {
            'process_name': 'DateTimeParserTestCase',
            'root_path': root_path,
            'data_dir': join(root_path, 'data'),
            'restfulpy_dir': join(root_path, '../../')
        }
        configure(context=context, force=True)

    def test_naive_datetime_parsing(self):
        # The application is configured to use system's local date and time.
        settings.timezone = None

        # Submit without timezone: accept and assume the local date and time.
        self.assertEquals(
            datetime(1970, 1, 1),
            parse_datetime('1970-01-01T00:00:00')
        )
        self.assertEquals(
            datetime(1970, 1, 1, microsecond=1000),
            parse_datetime('1970-01-01T00:00:00.001')
        )
        self.assertEquals(
            datetime(1970, 1, 1, microsecond=1000),
            parse_datetime('1970-01-01T00:00:00.001000')
        )

        # Timezone aware
        # Submit with 'Z' and or '+3:30':
        # accept and assume as the UTC, so we have to convert
        # it to local date and time before continuing the rest of process
        with mockup_localtimezone(tzoffset(None, 3600)):
            self.assertEquals(
                datetime(1970, 1, 1, 1),
                parse_datetime('1970-01-01T00:00:00Z')
            )

            self.assertEquals(
                datetime(1970, 1, 1, 1, 30),
                parse_datetime('1970-01-01T00:00:00-0:30')
            )

    def test_timezone_aware_datetime_parsing(self):
        # The application is configured to use a specific timezone
        settings.timezone = tzoffset('Tehran', 12600)
        with self.assertRaises(ValueError):
            parse_datetime('1970-01-01T00:00:00')

        self.assertEquals(
            datetime(1970, 1, 1, 3, 30, tzinfo=tzoffset('Tehran', 12600)),
            parse_datetime('1970-01-01T00:00:00Z')
        )

        self.assertEquals(
            datetime(1970, 1, 1, 4, 30, tzinfo=tzoffset('Tehran', 12600)),
            parse_datetime('1970-01-01T00:00:00-1:00')
        )

    def test_naive_datetime_formatting(self):
        # The application is configured to use system's local date and time.
        settings.timezone = None

        self.assertEqual(
            '1970-01-01T00:00:00',
            format_datetime(datetime(1970, 1, 1))
        )

        self.assertEqual(
            '1970-01-01T00:00:00.000001',
            format_datetime(datetime(1970, 1, 1, 0, 0, 0, 1))
        )

        with mockup_localtimezone(tzoffset(None, 3600)):
            self.assertEqual(
                '1970-01-01T00:00:00',
                format_datetime(
					datetime(1970, 1, 1, tzinfo=tzoffset(None, 3600))
				)
            )

    def test_timezone_aware_datetime_formatting(self):
        # The application is configured to use a specific timezone as the
        # default
        settings.timezone = tzoffset('Tehran', 12600)

        with self.assertRaises(ValueError):
            format_datetime(datetime(1970, 1, 1))

        self.assertEqual(
            '1970-01-01T00:00:00+03:30',
            format_datetime(datetime(1970, 1, 1, tzinfo=tzoffset(None, 12600)))
        )

    def test_naive_unix_timestamp(self):
        # The application is configured to use system's local date and time.
        settings.timezone = None

        self.assertEquals(
            datetime(1970, 1, 1, 0, 0, 1, 334300),
            parse_datetime('1.3343')
        )

    def test_timezone_aware_unix_timestamp(self):
        # The application is configured to use a specific timezone as the
        # default
        settings.timezone = tzoffset('Tehran', 12600)


        self.assertEquals(
            datetime(
                1970, 1, 1, 3, 30, 1, 334300,
                tzinfo=tzoffset('Tehran', 12600)
            ),
            parse_datetime('1.3343')
        )



if __name__ == '__main__':  # pragma: no cover
    unittest.main()

