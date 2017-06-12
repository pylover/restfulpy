import sys
import warnings
import importlib
import importlib.util
import uuid
import re
from os.path import dirname, abspath
from datetime import datetime, timedelta
from hashlib import md5


ZERO = timedelta(0)


def import_python_module_by_filename(name, module_filename):
    """
    Import's a file as a python module, with specified name.

    Don't ask about the `name` argument, it's required.
    
    :param name: The name of the module to override upon imported filename.
    :param module_filename: The filename to import as a python module.
    :return: The newly imported python module.
    """

    sys.path.append(abspath(dirname(module_filename)))
    spec = importlib.util.spec_from_file_location(
        name,
        location=module_filename)
    imported_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(imported_module)
    return imported_module


def construct_class_by_name(name, *args, **kwargs):
    """
    Construct a class by module path name using *args and **kwargs

    Don't ask about the `name` argument, it's required.

    :param name: class name
    :return: The newly imported python module.
    """
    parts = name.split('.')
    module_name, class_name = '.'.join(parts[:-1]), parts[-1]
    module = importlib.import_module(module_name)
    return getattr(module, class_name)(*args, **kwargs)


def deprecated(func):
    """
    This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used.
    """

    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # Turn off filter
        warnings.warn(
            'Call to deprecated function %s.' % func.__name__,
            category=DeprecationWarning,
            stacklevel=2
        )
        warnings.simplefilter('default', DeprecationWarning)  # Reset filter
        return func(*args, **kwargs)

    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


def format_iso_datetime(stamp):
    """ Return a string representing the date and time in ISO 8601 format.
        If the time is in UTC, adds a 'Z' directly after the time without
        a space.

        see http://en.wikipedia.org/wiki/ISO_8601.

        >>> class EET(tzinfo):
        ...     def utcoffset(self, dt):
        ...         return timedelta(minutes=120)
        ...     def dst(self, dt):
        ...         return timedelta()
        >>> format_iso_datetime(datetime(2012, 2, 22, 12, 52, 29, 300))
        '2012-02-22T12:52:29'
        >>> format_iso_datetime(datetime(2012, 2, 22, 12, 52, 29, 300,
        ...     tzinfo=UTC))
        '2012-02-22T12:52:29Z'
        >>> format_iso_datetime(datetime(2012, 2, 22, 12, 52, 29, 300,
        ...     tzinfo=EET()))
        '2012-02-22T12:52:29+02:00'
    """
    if stamp.tzinfo:
        if stamp.utcoffset() == ZERO:
            return datetime(*stamp.timetuple()[:6]).isoformat() + 'Z'
    if stamp.microsecond:
        stamp = stamp.replace(microsecond=0)
    return stamp.isoformat()


def format_iso_time(stamp):
    """ Return a string representing the time in ISO 8601 format.
        If the time is in UTC, adds a 'Z' directly after the time without
        a space.

        see http://en.wikipedia.org/wiki/ISO_8601.

        >>> class EET(tzinfo):
        ...     def utcoffset(self, dt):
        ...         return timedelta(minutes=120)
        ...     def dst(self, dt):
        ...         return timedelta()
        >>> format_iso_time(time(12, 52, 29, 300))
        '12:52:29'
        >>> format_iso_time(time(12, 52, 29, 300,
        ...     tzinfo=UTC))
        '12:52:29Z'
        >>> format_iso_time(time(12, 52, 29, 300,
        ...     tzinfo=EET()))
        '12:52:29+02:00'
    """
    if stamp.microsecond:
        stamp = stamp.replace(microsecond=0)
    if stamp.tzinfo:
        if stamp.utcoffset() == ZERO:
            return stamp.replace(tzinfo=None).isoformat() + 'Z'
        else:
            return stamp.isoformat()
    else:
        return stamp.isoformat()


def random_password(length=10):
    """Returns a random string of length string_length."""
    random = str(uuid.uuid4())  # Convert UUID format to a Python string.
    random = random.upper()  # Make all characters uppercase.
    random = random.replace("-", "")  # Remove the UUID '-'.
    return random[0:length]  # Return the random string.


def get_class_by_tablename(base, table_name):
    # noinspection PyProtectedMember
    for c in base._decl_class_registry.values():
        if hasattr(c, '__tablename__') and c.__tablename__ == table_name:
            return c


def to_camel_case(text):
    return re.sub("(_\w)", lambda x: x.group(1)[1:].upper(), text)


def copy_stream(source, target, *, chunk_size: int= 16 * 1024) -> int:
    length = 0
    while 1:
        buf = source.read(chunk_size)
        if not buf:
            break
        length += len(buf)
        target.write(buf)
    return length


def md5sum(f):
    if isinstance(f, str):
        file_obj = open(f, 'rb')
    else:
        file_obj = f

    try:
        checksum = md5()
        while True:
            d = file_obj.read(1024)
            if not d:
                break
            checksum.update(d)
        return checksum.digest()
    finally:
        if file_obj is not f:
            file_obj.close()
