import unittest
from datetime import datetime

from restfulpy.utils import parse_datetime


class DateTimeParseTestCase(unittest.TestCase):

    def test_naive_datetime_parsing(self):
        self.asserEqual(
            datetime(1970, 1, 1),
            parse_datetime('1970-01-01T00:00:00Z')
        )

