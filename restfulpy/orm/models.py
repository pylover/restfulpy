
import functools
from datetime import datetime, date, time
from decimal import Decimal

from nanohttp import context, HttpNotFound, HttpBadRequest
from sqlalchemy import Column, event
from sqlalchemy.orm import validates, Query, CompositeProperty, \
    RelationshipProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.ext.hybrid import HYBRID_PROPERTY
from sqlalchemy.ext.associationproxy import ASSOCIATION_PROXY
from sqlalchemy.inspection import inspect

from .field import ModelFieldInfo, Field
from .mixins import PaginationMixin, FilteringMixin, OrderingMixin
from ..utils import to_camel_case
from ..datetimehelpers import parse_datetime, format_datetime


class BaseModel(object):
    _key_serializer = None

    @classmethod
    def get_column(cls, column):
        if isinstance(column, str):
            mapper = inspect(cls)
            return mapper.columns[column]
        # Commented-out by vahid, because I cannot reach here by tests, I think it's not necessary at all.
        # if isinstance(column, SynonymProperty):
        #     return column.parent.columns[column.name]
        return column

    @classmethod
    def import_value(cls, column, v):
        c = cls.get_column(column)
        if isinstance(c, Column) or isinstance(c, InstrumentedAttribute):
            if c.type.python_type is bool and not isinstance(v, bool):
                return str(v).lower() == 'true'
        return v

    @classmethod
    def get_column_info(cls, column):
        # Use original property for proxies
        if hasattr(column, 'original_property') and column.original_property:
            info = column.info.copy()
            info.update(column.original_property.info)
        else:
            info = column.info

        return info

    @classmethod
    def prepare_for_export(cls, column, v):
        info = cls.get_column_info(column)
        param_name = info.get('json') or to_camel_case(column.key)

        if hasattr(column, 'property') \
                and isinstance(column.property, RelationshipProperty) \
                and column.property.uselist:
            result = [c.to_dict() for c in v]

        elif hasattr(column, 'property') \
            and isinstance(column.property, CompositeProperty):
            result = v.__composite_values__()

        elif v is None:
            result = v

        elif isinstance(v, (datetime, date, time)):
            result = format_datetime(v)

        elif hasattr(v, 'to_dict'):
            result = v.to_dict()

        elif isinstance(v, Decimal):
            result = str(v)

        else:
            result = v

        return param_name, result

    @classmethod
    def iter_metadata_fields(cls):
        for c in cls.iter_json_columns(
                relationships=True,
                include_readonly_columns=True,
                include_protected_columns=True
            ):
            yield from ModelFieldInfo.from_column(
                cls.get_column(c),
                info=cls.get_column_info(c)
            )

    @classmethod
    def json_metadata(cls):
        fields = {f.name: f.to_json() for f in cls.iter_metadata_fields()}
        mapper = inspect(cls)
        return {
            'name': cls.__name__,
            'primaryKeys': [c.key for c in mapper.primary_key],
            'fields': fields
        }

    def update_from_request(self):
        for column, value in self.extract_data_from_request():
            setattr(
                self,
                column.key[1:] if column.key.startswith('_') else column.key,
                self.import_value(column, value)
            )

    @classmethod
    def iter_columns(cls, relationships=True, synonyms=True, composites=True,
                     use_inspection=True, hybrids=True):
        if use_inspection:
            mapper = inspect(cls)
            for k, c in mapper.all_orm_descriptors.items():

                if k == '__mapper__':
                    continue

                if c.extension_type == ASSOCIATION_PROXY:
                    continue

                if (not hybrids and c.extension_type == HYBRID_PROPERTY) \
                        or (not relationships and k in mapper.relationships) \
                        or (not synonyms and k in mapper.synonyms) \
                        or (not composites and k in mapper.composites):
                    continue

                yield getattr(cls, k)

        else:
            # noinspection PyUnresolvedReferences
            for c in cls.__table__.c:
                yield c

    @classmethod
    def iter_json_columns(cls, include_readonly_columns=True,
                          include_protected_columns=False, **kw):
        for c in cls.iter_columns(**kw):

            info = cls.get_column_info(c)
            if (not include_protected_columns and info.get('protected')) or \
                    (not include_readonly_columns and info.get('readonly')):
                continue

            yield c

    @classmethod
    def extract_data_from_request(cls):
        for c in cls.iter_json_columns(
                include_protected_columns=True,
                include_readonly_columns=False
        ):
            param_name = c.info.get('json', to_camel_case(c.key))
#            import pudb; pudb.set_trace()  # XXX BREAKPOINT

            if param_name in context.form:

                if hasattr(c, 'property') and hasattr(c.property, 'mapper'):
                    raise HttpBadRequest('Invalid attribute')

                value = context.form[param_name]
                # Ensuring the python type, and ignoring silently if the
                # python type is not specified
                try:
                    c.type.python_type
                except NotImplementedError:
                    yield c, value
                    continue

                # Parsing date and or time if required.
                if c.type.python_type in (datetime, date, time):
                    try:
                        yield c, parse_datetime(value)
                    except ValueError:
                        raise HttpBadRequest('Invalid date or time format')
                else:
                    yield c, value

    def to_dict(self):
        result = {}
        for c in self.iter_json_columns():
            result.setdefault(*self.prepare_for_export(c, getattr(self, c.key)))
        return result

    @classmethod
    def create_sort_criteria(cls, sort_columns):
        criteria = []
        columns = {
            c.info.get('json', to_camel_case(c.key)): c
            for c in cls.iter_json_columns()
        }
        for column_name, option in sort_columns:
            if column_name in columns:
                criteria.append((columns[column_name], option == 'desc'))
        return criteria

    # noinspection PyUnresolvedReferences
    @classmethod
    def filter_paginate_sort_query_by_request(cls, query=None):
        query = query or cls.query

        if issubclass(cls, FilteringMixin):
            query = cls.filter_by_request(query)

        if issubclass(cls, OrderingMixin):
            query = cls.sort_by_request(query)

        if issubclass(cls, PaginationMixin):
            query = cls.paginate_by_request(query=query)

        return query

    @classmethod
    def dump_query(cls, query=None):
        result = []
        for o in cls.filter_paginate_sort_query_by_request(query):
            result.append(o.to_dict())
        return result

    @classmethod
    def expose(cls, func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if result is None:
                raise HttpNotFound()
            if isinstance(result, Query):
                return cls.dump_query(result)
            return result

        return wrapper


@event.listens_for(BaseModel, 'class_instrument')
def receive_class_instrument(cls):
    for field in cls.iter_columns(relationships=False, synonyms=False, use_inspection=False):
        if not isinstance(field, Field) or not field.can_validate:
            continue
        method_name = 'validate_%s' % field.name
        if not hasattr(cls, method_name):
            def validator(self, key, value):
                return self.get_column(key).validate(value)

            setattr(cls, method_name, validates(field.name)(validator))
