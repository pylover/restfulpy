import re
from datetime import datetime

from nanohttp import context, HTTPBadRequest, settings
from sqlalchemy import DateTime, between, desc
from sqlalchemy.events import event
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.expression import nullslast, nullsfirst

from .field import Field


FILTERING_IN_OPERATOR_REGEX = re.compile(r'!?IN\((?P<items>.*)\)')
FILTERING_BETWEEN_OPERATOR_REGEX = \
    re.compile(r'!?BETWEEN\((?P<min>.*),(?P<max>.*)\)')


class TimestampMixin:
    created_at = Field(
        DateTime,
        nullable=False,
        json='createdAt',
        readonly=True,
        default=datetime.utcnow,
    )


class ModifiedMixin(TimestampMixin):
    modified_at = Field(
        DateTime,
        nullable=True,
        json='modifiedAt',
        readonly=True
    )

    @property
    def last_modification_time(self):
        return self.modified_at or self.created_at

    @staticmethod
    def before_update(mapper, connection, target):
        target.modified_at = datetime.utcnow()

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, 'before_update', cls.before_update)


class SoftDeleteMixin:
    removed_at = Field(
        DateTime,
        nullable=True,
        json='removedAt',
        readonly=True
    )

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
        self.removed_at = datetime.utcnow()

    def soft_undelete(self, ignore_errors=False):
        if not ignore_errors:
            self.assert_is_deleted()
        self.removed_at = None

    @staticmethod
    def before_delete(mapper, connection, target):
        raise AssertionError(f'Cannot remove {target}')

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, 'before_delete', cls.before_delete)

    @classmethod
    def filter_deleted(cls, query):
        return query.filter(cls.removed_at.isnot(None))

    @classmethod
    def exclude_deleted(cls, query):
        return query.filter(cls.removed_at.is_(None))


class ActivationMixin:

    activated_at = Field(
        DateTime,
        nullable=True,
        json='activatedAt',
        readonly=True,
        protected=True
    )

    @hybrid_property
    def is_active(self):
        return self.activated_at is not None

    @is_active.setter
    def is_active(self, value):
        self.activated_at = datetime.utcnow() if value else None

    @is_active.expression
    def is_active(self):
        return self.activated_at.isnot(None)

    @classmethod
    def filter_activated(cls, query):
        return query.filter(cls.is_active)

    @classmethod
    def import_value(cls, column, v):
        if column.key == cls.is_active.key and not isinstance(v, bool):
            return str(v).lower() == 'true'
        return super().import_value(column, v)


class AutoActivationMixin(ActivationMixin):

    activated_at = Field(
        DateTime,
        nullable=True,
        json='activatedAt',
        readonly=True,
        default=datetime.utcnow
    )


class DeactivationMixin(ActivationMixin):

    deactivated_at = Field(
        DateTime,
        nullable=True,
        json='deactivatedAt',
        readonly=True,
    )

    @ActivationMixin.is_active.setter
    def is_active(self, value):
        now = datetime.utcnow()
        if value:
            self.activated_at = now
            self.deactivated_at = None
        else:
            self.activated_at = None
            self.deactivated_at = now


class PaginationMixin:
    __take_header_key__ = 'HTTP_X_TAKE'
    __skip_header_key__ = 'HTTP_X_SKIP'
    __max_take__ = 100

    @classmethod
    def paginate_by_request(cls, query):

        try:
            take = int(
                context.query.get('take') \
                or context.environ.get(cls.__take_header_key__) \
                or cls.__max_take__
            )

            skip = int(
                context.query.get('skip') \
                or context.environ.get(cls.__skip_header_key__) \
                or 0
            )
        except ValueError:
            raise HTTPBadRequest()

        if take > cls.__max_take__:
            raise HTTPBadRequest()

        context.response_headers.add_header('X-Pagination-Take', str(take))
        context.response_headers.add_header('X-Pagination-Skip', str(skip))
        context.response_headers.add_header(
            'X-Pagination-Count',
            str(query.count())
        )
        return query.offset(skip).limit(take)


class FilteringMixin:
    @classmethod
    def filter_by_request(cls, query):

        for c in cls.iter_json_columns():
            json_name = cls.get_column_info(c)['json']
            if json_name in context.query:
                value = context.query[json_name]
                query = cls._filter_by_column_value(query, c, value)

        return query

    @classmethod
    def _filter_by_column_value(cls, query, column, value):

        def return_(e):
            return query.filter(e)

        import_value = getattr(cls, 'import_value')
        if not isinstance(value, str):
            raise HTTPBadRequest()

        in_operator_match = FILTERING_IN_OPERATOR_REGEX.match(value)
        if in_operator_match:
            not_ = value.startswith('!')
            items = in_operator_match.groupdict()['items'].split(',')
            items = [i for i in items if i.strip() != '']
            if not len(items):
                raise HTTPBadRequest('Invalid query string: %s' % value)
            expression = column.in_([import_value(column, j) for j in items])
            if not_:
                expression = ~expression

            return return_(expression)

        between_operator_match = FILTERING_BETWEEN_OPERATOR_REGEX.match(value)
        if between_operator_match:
            not_ = value.startswith('!')
            groups = between_operator_match.groupdict()
            start, end = groups['min'].strip(), groups['max'].strip()
            if not (start or end):
                raise HTTPBadRequest('Invalid query string: %s' % value)
            expression = between(column, start, end)
            if not_:
                expression = ~expression

            return return_(expression)

        if value == 'null':
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

        # LIKE
        elif '%' in value:
            func, actual_value = \
                (column.ilike, value[1:]) if value.startswith('~') \
                else (column.like, value)
            expression = func(import_value(column, actual_value))

        # EQUAL
        else:
            expression = column == import_value(column, value)

        return return_(expression)


class OrderingMixin:
    @classmethod
    def _sort_by_key_value(cls, query, column, descending=False):
        expression = column

        if descending:
            expression = desc(expression)

        if settings.db.url.startswith('sqlite'):
            return query.order_by(expression)

        return query.order_by(
            (nullsfirst if descending else nullslast)(expression)
        )

    @classmethod
    def sort_by_request(cls, query):
        sort_exp = context.query.get('sort', '').strip()
        if not sort_exp:
            return query

        sort_columns = [
            (
                c[1:] if c.startswith('-') else c,
                'desc' if c.startswith('-') else 'asc'
            )
            for c in sort_exp.split(',')
        ]

        criteria = cls.create_sort_criteria(sort_columns)

        for criterion in criteria:
            query = cls._sort_by_key_value(query, *criterion)

        return query


class ApproveRequiredMixin:
    approved_at = Field(
        DateTime,
        nullable=True,
        json='approvedAt',
        readonly=True
    )

    @hybrid_property
    def is_approved(self):
        return self.approved_at is not None

    @is_approved.setter
    def is_approved(self, value):
        self.approved_at = datetime.utcnow() if value else None

    @is_approved.expression
    def is_approved(self):
        return self.approved_at.isnot(None)

    @classmethod
    def import_value(cls, column, v):
        if column.key == cls.is_approved.key and not isinstance(v, bool):
            return str(v).lower() == 'true'
        return super().import_value(column, v)

    @classmethod
    def filter_approved(cls, query=None, session=None):
        if query is None:
            query = session.query(cls) if session else cls.query
        return query.filter(cls.is_approved)


class FullTextSearchMixin:
    __ts_vector__ = None

    @classmethod
    def search(cls, expressions, query):
        expressions = expressions.replace(' ', '|')
        return query.filter(
            cls.__ts_vector__.match(expressions)
        )

