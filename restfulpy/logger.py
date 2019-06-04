import sys
import traceback
import functools

DEBUG = 1
INFO = 2
WARNING = 3
ERROR = 4

level = DEBUG


def error(ex):
    message = None
    traceback_ = None
    if isinstance(ex, str):
        message = ex
        type_, ex, traceback_ = sys.exc_info()
    else:
        type_ = type(ex)

    traceback.print_exception(type_, ex, traceback_, file=sys.stderr)
    if message:
        print(message, file=sys.stderr)


def log(severity, message):
    if level <= severity:
        print(message)


debug = functools.partial(log, DEBUG)
info = functools.partial(log, INFO)
warning = functools.partial(log, WARNING)

