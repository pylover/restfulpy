import time
import traceback
from datetime import datetime

from sqlalchemy import Integer, Enum, Unicode, DateTime, or_, and_
from sqlalchemy.sql.expression import text
from nanohttp import settings

from restfulpy.orm import TimestampMixin, DeclarativeBase, Field, DBSession, create_thread_unsafe_session
from restfulpy.exceptions import RestfulException
from restfulpy.logging_ import get_logger

logger = get_logger('taskqueue')


class TaskPopError(RestfulException):
    pass


class Task(TimestampMixin, DeclarativeBase):
    __tablename__ = 'task'

    id = Field(Integer, primary_key=True, json='id')
    priority = Field(Integer, nullable=False, default=50, json='priority')
    status = Field(Enum('new', 'success', 'in-progress', 'failed', name='task_status_enum'), default='new',
                   nullable=True, json='status')
    fail_reason = Field(Unicode(2048), nullable=True, json='reason')
    started_at = Field(DateTime, nullable=True, json='startedAt')
    terminated_at = Field(DateTime, nullable=True, json='terminatedAt')
    type = Field(Unicode(50))

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'polymorphic_on': type
    }

    def do_(self, context):
        raise NotImplementedError

    @classmethod
    def pop(cls, statuses={'new'}, include_types=None, exclude_types=None, filters=None, session=DBSession):

        find_query = session.query(cls.id.label('id'), cls.created_at, cls.status, cls.type, cls.priority)
        if filters is not None:
            find_query = find_query.filter(text(filters) if isinstance(filters, str) else filters)

        if include_types is not None:
            find_query = find_query.filter(or_(*[cls.type == task_type for task_type in include_types]))

        if exclude_types is not None:
            find_query = find_query.filter(and_(*[cls.type != task_type for task_type in exclude_types]))

        find_query = find_query \
            .filter(or_(*[cls.status == status for status in statuses])) \
            .order_by(cls.priority.desc()) \
            .order_by(cls.created_at) \
            .limit(1) \
            .with_lockmode('update') \
            .cte('find_query')

        update_query = Task.__table__.update() \
            .where(Task.id == find_query.c.id) \
            .values(status='in-progress') \
            .returning(Task.__table__.c.id)

        task_id = session.execute(update_query).fetchone()
        session.commit()
        if not task_id:
            raise TaskPopError('There is no task to pop')
        task_id = task_id[0]
        task = cls.query.filter(cls.id == task_id).one()
        return task

    def execute(self, context, session=DBSession):
        try:
            isolated_task = session.query(Task).filter(Task.id == self.id).one()
            isolated_task.do_(context)
            session.commit()
        except:
            session.rollback()
            raise

    @classmethod
    def cleanup(cls, session=DBSession):
        session.query(Task) \
            .filter(Task.status == 'in-progress') \
            .with_lockmode('update') \
            .update({'status': 'new', 'started_at': None, 'terminated_at': None})

    @classmethod
    def reset_status(cls, task_id, session=DBSession):
        session.query(Task) \
            .filter(Task.status == 'in-progress') \
            .filter(Task.id == task_id) \
            .with_lockmode('update') \
            .update({'status': 'new', 'started_at': None, 'terminated_at': None})


def worker(statuses={'new'}, include_types=None, exclude_types=None, filters=None):
    isolated_session = create_thread_unsafe_session()
    context = {'counter': 0}
    while True:
        context['counter'] += 1
        logger.info("Trying to pop a task, Counter: %s" % context['counter'])
        # noinspection PyBroadException
        try:
            task = Task.pop(
                include_types=include_types,
                exclude_types=exclude_types,
                statuses=statuses,
                filters=filters,
                session=isolated_session
            )

            task.execute(context)

            # Task success
            task.status = 'success'
            task.terminated_at = datetime.now()

        except TaskPopError:
            logger.info('No task to pop')
            isolated_session.rollback()

        except:
            logger.exception('Error when executing task: %s' % task.id)
            task.status = 'failed'
            task.fail_reason = traceback.format_exc()

        finally:
            if isolated_session.is_active:
                isolated_session.commit()

        time.sleep(settings.worker.gap)
