import functools

from sqlalchemy.orm import Query

from restfulpy.orm import PaginationMixin, FilteringMixin


def _serialize(query, sorting=False, type_=None):

    if isinstance(query, Query):

        if not type_:
            raise ValueError('The `model_class` keyword argument is not provided')

        if issubclass(type_, FilteringMixin):
            query = type_.filter_by_request(query)

        if sorting:
            query = type_.sort_by_request(query)

        if issubclass(type_, PaginationMixin):
            query = type_.paginate_by_request(query=query)

        query = [o.to_dict() for o in query]

    return query


def jsonify(*a, **options):

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return _serialize(func(*args, **kwargs), **options)

        return wrapper

    return decorator(a[0]) if a and callable(a[0]) else decorator
