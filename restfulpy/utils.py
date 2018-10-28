import importlib.util
import re
import sys
import warnings
from hashlib import md5
from os.path import dirname, abspath


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


def deprecated(func):  # pragma: no cover
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


def to_camel_case(text):
    return re.sub(r'(_\w)', lambda x: x.group(1)[1:].upper(), text)


def to_pascal_case(text):
    return to_camel_case(text).capitalize()


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

