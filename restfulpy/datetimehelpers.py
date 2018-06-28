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


def parse_datetime(value) -> datetime:
    """Parses a string a a datetime object

    The reason of wrapping this functionality is to preserve compatibillity
    and future exceptions handling.

    Another reason is to behave depend to the configuration when parsing date
    and time.
    """
    timezone = configuredtimezone()
    parsed_value = parse(value)

    if timezone is not None:
        # The application is configured to use UTC or another time zone:

        # Submit without timezone: Reject and tell the user to specify the
        # timezone.
        if parsed_value.tzinfo is None:
            raise ValueError('You have to specify the timezone')

        # The parsed value is a timezone aware object.
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


def format_datetime(value):
    timezone = configuredtimezone()
    if timezone is None and value.tzinfo is not None:
        # The output shoudn't have a timezone specifier.
        # So, converting it to system's local time
        value = value.astimezone(localtimezone()).replace(tzinfo=None)

    elif timezone is not None:
        if value.tzinfo is None:
            raise ValueError('The value must have a timezone specifier')

        elif value.tzinfo.utcoffset() != timezone.utcoffset():
            value = value.astimezone(timezone)

    result = value.isoformat()
    if result.endswith('+00:00'):
        result = f'{value[:-6]}Z'

    return result

