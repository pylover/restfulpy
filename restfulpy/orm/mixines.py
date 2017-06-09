
from datetime import datetime

from sqlalchemy import DateTime, Integer, between, desc
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import synonym, SynonymProperty
from sqlalchemy.sql.expression import nullslast, nullsfirst
from sqlalchemy.events import event
from nanohttp import context, HttpBadRequest, HttpConflict

from restfulpy.orm.field import Field
from restfulpy.utils import to_camel_case


class TimestampMixin:
    created_at = Field(DateTime, default=datetime.now, nullable=False, json='createdAt', readonly=True)


class ModifiedMixin(TimestampMixin):
    modified_at = Field(DateTime, nullable=True, json='modifiedAt', readonly=True)

    @property
    def last_modification_time(self):
        return self.modified_at or self.created_at

    # noinspection PyUnusedLocal
    @staticmethod
    def on_update(mapper, connection, target):
        target.modified_at = datetime.now()

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, 'before_update', cls.on_update)


class OrderableMixin:
    order = Field("order", Integer, default=0, nullable=False)
    __mapper_args__ = dict(order_by=order)

    @classmethod
    def apply_default_sort(cls, query):
        return query.order_by(cls.order)


class SoftDeleteMixin:
    removed_at = Field(DateTime, nullable=True, json='removedAt', readonly=True)

    def assert_is_not_deleted(self):
        if self.is_deleted:
            raise ValueError('Object is already deleted.')

    def assert_is_deleted(self):
        if not self.is_deleted:
            raise ValueError('Object is not deleted.')

    @property
    def is_deleted(self):
        return self.removed_at is not None

    def soft_delete(self, ignore_errors=False):
        if not ignore_errors:
            self.assert_is_not_deleted()
        self.removed_at = datetime.now()

    def soft_undelete(self, ignore_errors=False):
        if not ignore_errors:
            self.assert_is_deleted()
        self.removed_at = None

    @staticmethod
    def on_delete(mapper, connection, target):
        raise HttpConflict('Cannot remove this object: %s' % target)

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, 'before_delete', cls.on_delete)

    @classmethod
    def filter_deleted(cls, query=None):
        # noinspection PyUnresolvedReferences
        return (query or cls.query).filter(cls.removed_at.isnot(None))

    @classmethod
    def exclude_deleted(cls, query=None):
        # noinspection PyUnresolvedReferences
        return (query or cls.query).filter(cls.removed_at.is_(None))


class ActivationMixin:
    activated_at = Field(DateTime, nullable=True, json='activatedAt', readonly=True, protected=True)

    def _get_is_active(self):
        return self.activated_at is not None

    def _set_is_active(self, v):
        self.activated_at = datetime.now() if v else None

    # noinspection PyMethodParameters
    @declared_attr
    def is_active(cls):
        return synonym(
            'activated_at',
            descriptor=property(cls._get_is_active, cls._set_is_active),
            info=dict(json='isActive')
        )

    @classmethod
    def filter_activated(cls, query=None):
        # noinspection PyUnresolvedReferences
        return (query or cls.query).filter(cls.activated_at.isnot(None))

    @classmethod
    def import_value(cls, column, v):
        if column.key == cls.is_active.key and not isinstance(v, bool):
            return str(v).lower() == 'true'
        return super().import_value(column, v)


class PaginationMixin:
    __take_header_key__ = 'X_TAKE'
    __skip_header_key__ = 'X_SKIP'
    __max_take__ = 100

    @classmethod
    def paginate_by_request(cls, query=None):
        # noinspection PyUnresolvedReferences
        query = query or cls.query

        try:
            take = int(context.query_string.get('take') or context.environ.get(cls.__take_header_key__) or cls.__max_take__)
        except ValueError:
            take = cls.__max_take__

        try:
            skip = int(context.query_string.get('skip') or context.environ.get(cls.__skip_header_key__) or 0)
        except ValueError:
            skip = 0

        if take > cls.__max_take__:
            raise HttpBadRequest()

        context.response_headers.add_header('X-Pagination-Take', str(take))
        context.response_headers.add_header('X-Pagination-Skip', str(skip))
        context.response_headers.add_header('X-Pagination-Count', str(query.count()))
        return query.offset(skip).limit(take)  # [skip:skip + take] Commented by vahid


class FilteringMixin:

    @classmethod
    def filter_by_request(cls, query=None):
        # noinspection PyUnresolvedReferences
        query = query or cls.query

        # noinspection PyUnresolvedReferences
        for c in cls.iter_json_columns():
            json_name = c.info.get('json', to_camel_case(c.key))
            if json_name in context.query_string:
                value = context.query_string[json_name]
                query = cls._filter_by_column_value(query, c, value)

        return query

    @classmethod
    def _filter_by_column_value(cls, query, column, value):

        import_value = getattr(cls, 'import_value')

        if value.startswith('^') or value.startswith('!^'):
            if isinstance(value, str):
                value = value.split(',')
            not_ = value[0].startswith('!^')
            first_item = value[0][2 if not_ else 1:]
            items = [first_item] + value[1:]
            items = [i for i in items if i.strip()]
            if not len(items):
                raise HttpBadRequest('Invalid query string: %s' % value)
            expression = column.in_([import_value(column, j) for j in items])
            if not_:
                expression = ~expression

        elif not isinstance(value, str) or value.startswith('~'):
            if isinstance(value, str):
                values = value[1:].split(',')
            else:
                values = value
            start, end = [import_value(column, v) for v in values]
            expression = between(column, start, end)

        elif value == 'null':
            expression = column.is_(None)
        elif value == '!null':
            expression = column.isnot(None)
        elif value.startswith('!'):
            expression = column != import_value(column, value[1:])
        elif value.startswith('>='):
            expression = column >= import_value(column, value[2:])
        elif value.startswith('>'):
            expression = column > import_value(column, value[1:])
        elif value.startswith('<='):
            expression = column <= import_value(column, value[2:])
        elif value.startswith('<'):
            expression = column < import_value(column, value[1:])
        elif value.startswith('%~'):
            expression = column.ilike('%%%s%%' % import_value(column, value[2:]))
        elif value.startswith('%'):
            expression = column.like('%%%s%%' % import_value(column, value[1:]))
        else:
            expression = column == import_value(column, value)

        return query.filter(expression)


class OrderingMixin:

    @classmethod
    def _sort_by_key_value(cls, query, column, descending=False):

        if isinstance(column, SynonymProperty):
            expression = column.parent.columns[column.name]
        else:
            expression = column

        if descending:
            expression = desc(expression)
            pre = nullsfirst
        else:
            pre = nullslast

        return query.order_by(pre(expression))

    @classmethod
    def sort_by_request(cls, query=None):
        # noinspection PyUnresolvedReferences
        query = query or cls.query

        sort_exp = context.query_string.get('sort', '').strip()
        if not sort_exp:
            if issubclass(cls, OrderableMixin):
                return cls.apply_default_sort(query)
            return query

        sort_columns = {c[1:] if c.startswith('-') else c: 'desc' if c.startswith('-') else 'asc'
                        for c in sort_exp.split(',')}

        criteria = cls.create_sort_criteria(sort_columns)

        for criterion in criteria:
            query = cls._sort_by_key_value(query, *criterion)

        return query


class ApproveRequiredMixin:
    approved_at = Field(DateTime, nullable=True, json='approvedAt', readonly=True)

    def _get_is_approved(self):
        return self.approved_at is not None

    def _set_is_approved(self, v):
        self.approved_at = datetime.now() if v else None

    # noinspection PyMethodParameters
    @declared_attr
    def is_approved(cls):
        return synonym(
            '_is_approved',
            descriptor=property(cls._get_is_approved, cls._set_is_approved),
            info=dict(json='isApproved')
        )

    @classmethod
    def approved_objects(cls, query=None):
        # noinspection PyUnresolvedReferences
        return (query or cls.query).filter(cls.activated_at.isnot(None))


class FullTextSearchMixin:
    __ts_vector__ = None

    @classmethod
    def search(cls, expressions, query=None):
        expressions = expressions.replace(' ', '|')
        query = (query or cls.query).filter(
            cls.__ts_vector__.match(expressions)
        )
        return query
