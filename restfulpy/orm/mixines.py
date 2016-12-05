
from datetime import datetime

from sqlalchemy import DateTime, Integer
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import synonym
from sqlalchemy.events import event

from restfulpy.orm.field import Field
from restfulpy.exceptions import OrmException


class TimestampMixin(object):
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


class OrderableMixin(object):
    order = Field("order", Integer, default=0, nullable=False)
    __mapper_args__ = dict(order_by=order)


class SoftDeleteMixin(object):
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
        raise OrmException('Cannot remove this object: %s' % target)

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, 'before_delete', cls.on_delete)

    @classmethod
    def exclude_deleted(cls, query=None):
        return (query or cls.query).filter(cls.removed_at.is_(None))

    @classmethod
    def filter_deleted(cls, query=None):
        return (query or cls.query).filter(cls.removed_at.isnot(None))



class ActivationMixin(object):
    activated_at = Field(DateTime, nullable=True, json='activatedAt', readonly=True, protected=True)

    def _get_is_active(self):
        return self.activated_at is not None

    def _set_is_active(self, v):
        self.activated_at = datetime.now() if v else None

    @declared_attr
    def is_active(cls):
        return synonym(
            '_is_active',
            descriptor=property(cls._get_is_active, cls._set_is_active),
            info=dict(json='isActive')
        )

    @classmethod
    def filter_activated(cls, query=None):
        return (query or cls.query).filter(cls.activated_at.isnot(None))
