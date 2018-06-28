import unittest
from datetime import datetime
from dateutil.tz import tzutc

from restfulpy.utils import parse_datetime


class DateTimeParseTestCase(unittest.TestCase):

    def test_naive_datetime_parsing(self):
        self.ensure_asserts((
            (
                datetime(1970, 1, 1, tzinfo=tzutc(0)),
                parse_datetime('1970-01-01T00:00:00Z')),
        ))

    def ensure_asserts(self, asserts):
        for equality in asserts:
            self.assertEqual(*equality)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()

