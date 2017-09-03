import re

ISO_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
ISO_DATETIME_PATTERN = re.compile('^(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d*)?Z?$')
ISO_DATE_FORMAT = '%Y-%m-%d'
