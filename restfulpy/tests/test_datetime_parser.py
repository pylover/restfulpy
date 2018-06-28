import unittest
from datetime import datetime, timedelta
from dateutil.tz import tzutc, tzoffset
from os.path import dirname, join

from restfulpy.datetimehelpers import parse_datetime
from restfulpy.configuration import configure
from restfulpy.testing import localtimezone_mockup


class DateTimeParserTestCase(unittest.TestCase):

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
        # Naive
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
        with localtimezone_mockup(tzoffset(None, 3600)):
            self.assertEquals(
                datetime(1970, 1, 1, 1),
                parse_datetime('1970-01-01T00:00:00Z')
            )

            self.assertEquals(
                datetime(1970, 1, 1, 1, 30),
                parse_datetime('1970-01-01T00:00:00-0:30')
            )



#    def test_timezone_aware_datetime_parsing(self):
#        self.ensure_asserts((
#            # Timezone aware
#            (
#                datetime(1970, 1, 1, tzinfo=tzutc(0)),
#                parse_datetime('1970-01-01T00:00:00Z')
#            ),
#            (
#                datetime(1970, 1, 1, tzinfo=tzoffset(None, 5400)),
#                parse_datetime('1970-01-01T00:00:00+1:30')
#            ),
#        ))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()

