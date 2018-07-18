import sys
import pytest
from bddrest import HTTPStatus
from bddrest.proxy import ObjectProxy
from nanohttp import HTTPBadRequest, HTTPStatus as HTTPError


class HTTPStatusRaises():
    _context = None

    def __init__(self, exception):
        self.exception = exception

    def __enter__(self):
        return ObjectProxy(self._resolver)

    def __exit__(self, exc_type, exc, traceback):
        import pudb; pudb.set_trace()  # XXX BREAKPOINT
        if issubclass(exc_type, self.exception):
            self._raised_exception = exc
            sys.exc_clear()
        else:
            raise exc

    def _resolver(self):
        return self._raised_exception


def my_awesome_function_which_raises_an_exception():
    raise HTTPBadRequest()


def test_http_status_raises():
    with HTTPStatusRaises(HTTPError) as ex:
        my_awesome_function_which_raises_an_exception()

    import pudb; pudb.set_trace()  # XXX BREAKPOINT
    assert ex is not None

