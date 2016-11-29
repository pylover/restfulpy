
from sqlalchemy import Integer, Enum, Unicode, DateTime, or_, and_
from sqlalchemy.sql.expression import text

from restfulpy.orm import TimestampMixin, DeclarativeBase, Field, DBSession
from restfulpy.exceptions import RestfulException


class TaskPopError(RestfulException):
    pass


class Task(TimestampMixin, DeclarativeBase):
    __tablename__ = 'task'

    id = Field(Integer, primary_key=True, json='id', unreadable=True)
    priority = Field(Integer, nullable=False, default=50, json='priority')
    resolution = Field(Enum('new', 'success', 'in-progress', 'failed', name='task_resolution_enum'),
                       nullable=True, json='resolution')
    fail_reason = Field(Unicode(2048), nullable=True, json='reason')
    started_at = Field(DateTime, nullable=True, json='startedAt')
    terminated_at = Field(DateTime, nullable=True, json='terminatedAt')
    type = Field(Unicode(50))

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'polymorphic_on': type
    }

    @classmethod
    def schedule(cls, *args, **kwargs):
        raise NotImplementedError

    def do_(self, context):
        raise NotImplementedError

    @classmethod
    def pop(cls, resolutions={'new'}, include_types=None, exclude_types=None, filters=None):
        try:
            find_query = cls.query
            if filters:
                find_query = find_query.filter(text(filters))
            if include_types:
                find_query = find_query.filter(or_(*[cls.type == task_type for task_type in include_types]))
            if exclude_types:
                find_query = find_query.filter(and_(*[cls.type != task_type for task_type in exclude_types]))
            find_query = find_query \
                .filter(or_(*[cls.resolution == resolution for resolution in resolutions])) \
                .order_by(cls.priority.desc()) \
                .order_by(cls.created_at)\
                .limit(1)\
                .with_lockmode('update') \
                .cte('find_query')

            update_query = Task.__table__.update()\
                .where(Task.id == find_query.c.id) \
                .values(resolution='in-progress') \
                .returning(Task.__table__.c.id)

            task_id = DBSession.execute(update_query).fetchall()
            DBSession.commit()

            try:
                task_id = task_id[0][0]
            except IndexError:
                return None

            return Task.query.filter(Task.id == task_id).one_or_none()

        except Exception as ex:
            raise TaskPopError(ex)
