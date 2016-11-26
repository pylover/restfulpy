import functools

from sqlalchemy.orm import Query


def _serialize(obj, pagination=False, filtering=False, sorting=False, type=None):

    if isinstance(obj, Query):

        if not type:
            raise ValueError('The `model_class` keyword argument is not provided')

        if filtering:
            obj = type.filter_by_request(obj)

        if sorting:
            obj = type.sort_by_request(obj)

        if pagination:
            obj = type.paginate_by_request(obj)

        obj = [o.to_dict() for o in obj]

    return obj


def serialize(**options):

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return _serialize(func(*args, **kwargs), **options)

        return wrapper
    return decorator
