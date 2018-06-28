from datetime import datetime, tzinfo

from dateutil.parser import parse
from dateutil.tz import tzutc, tzstr, tzlocal

from .configuration import settings


def localtimezone():
    return tzlocal()


def configuredtimezone():
    timezone = settings.timezone
    if timezone in ('', None):
        return None

    if isinstance(timezone, tzinfo):
        return timezone

    if timezone in (0, 'utc', 'UTC', 'Z', 'z'):
        return tzutc()

    if isinstance(timezone, str):
        return tzstr(timezone)

    raise ValueError(f'Invalid timezone in configuration: {timezone}')


def now():
    timezone = configuredtimezone()
    if timezone is not None:
        return datetime.now(timezone)

    return datetime.now()


def parse_datetime(value):
    """The reason of wrapping this functionality is to preserve compatibillity
    and future exceptions handling.
    """
    timezone = configuredtimezone()
    parsed_value = parse(value)

    if not timezone:
        # The application is configured to use system's local timezone

        if parsed_value.tzinfo:
            # The sumittd value has tzinfo.
            # So converting it to system's local and removing the tzinfo
            # to achieve a naive object.
            parsed_value = parsed_value\
                .astimezone(localtimezone())\
                .replace(tzinfo=None)

    return parsed_value

