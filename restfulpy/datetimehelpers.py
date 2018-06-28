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

    if timezone:
        # The application is configured to use UTC or another time zone:

        # Submit without timezone: Reject and tell the user to specify the
        # timezone.
        if parsed_value.tzinfo is None:
            raise ValueError('You have to specify the timezone')

        # The parsed value is a timezone aware value
        # If ends with Z: accept and assume as the UTC
        # Then converting it to configured timezone and continue the
        # rest of process
        parsed_value = parsed_value.astimezone(timezone)


    elif parsed_value.tzinfo:
        # The application is configured to use system's local timezone
        # And the sumittd value has tzinfo.
        # So converting it to system's local and removing the tzinfo
        # to achieve a naive object.
        parsed_value = parsed_value\
            .astimezone(localtimezone())\
            .replace(tzinfo=None)

    return parsed_value

