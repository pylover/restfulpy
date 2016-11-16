
import functools

from nanohttp import context, HttpUnauthorized


def authorize(*roles):

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            identity = context.identity
            if not identity or not identity.is_in_roles(*roles):
                raise HttpUnauthorized()

            return func(*args, **kwargs)

        return wrapper

    return decorator
