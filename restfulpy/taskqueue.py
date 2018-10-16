import time
import traceback
from datetime import datetime

from nanohttp import settings
from sqlalchemy import Integer, Enum, Unicode, DateTime
from sqlalchemy.sql.expression import text

from restfulpy.exceptions import RestfulException
from restfulpy.logging_ import get_logger
from restfulpy.orm import TimestampMixin, DeclarativeBase, Field, DBSession, \
    create_thread_unsafe_session


logger = get_logger('taskqueue')


class TaskPopError(RestfulException):
    pass


class RestfulpyTask(TimestampMixin, DeclarativeBase):
    __tablename__ = 'restfulpy_task'

    id = Field(Integer, primary_key=True, json='id')
    priority = Field(Integer, nullable=False, default=50, json='priority')
    status = Field(
        Enum(
            'new',
            'success',
            'in-progress',
            'failed',
            name='task_status_enum'
        ),
        default='new',
        nullable=True, json='status'
    )
    fail_reason = Field(Unicode(4096), nullable=True, json='reason')
    started_at = Field(DateTime, nullable=True, json='startedAt')
    terminated_at = Field(DateTime, nullable=True, json='terminatedAt')
    type = Field(Unicode(50))

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'polymorphic_on': type
    }

    def do_(self):  # pragma: no cover
        raise NotImplementedError

    @classmethod
    def pop(cls, statuses={'new'}, filters=None, session=DBSession):

        find_query = session.query(
            cls.id.label('id'),
            cls.created_at,
            cls.status,
            cls.type,
            cls.priority
        )
        if filters is not None:
            find_query = find_query.filter(
                text(filters) if isinstance(filters, str) else filters
            )

        find_query = find_query \
            .filter(cls.status.in_(statuses)) \
            .order_by(cls.priority.desc()) \
            .order_by(cls.created_at) \
            .limit(1) \
            .with_for_update()

        cte = find_query.cte('find_query')

        update_query = RestfulpyTask.__table__.update() \
            .where(RestfulpyTask.id == cte.c.id) \
            .values(status='in-progress') \
            .returning(RestfulpyTask.__table__.c.id)

        task_id = session.execute(update_query).fetchone()
        session.commit()
        if not task_id:
            raise TaskPopError('There is no task to pop')
        task_id = task_id[0]
        task = session.query(cls).filter(cls.id == task_id).one()
        return task

    def execute(self, context, session=DBSession):
        try:
            isolated_task = session \
                .query(RestfulpyTask) \
                .filter(RestfulpyTask.id == self.id) \
                .one()
            isolated_task.do_(context)
            session.commit()
        except:
            session.rollback()
            raise

    @classmethod
    def cleanup(cls, session=DBSession, filters=None, statuses=['in-progress']):
        cleanup_query = session.query(RestfulpyTask) \
            .filter(RestfulpyTask.status.in_(statuses))

        if filters is not None:
            cleanup_query = cleanup_query.filter(
                text(filters) if isinstance(filters, str) else filters
            )

        cleanup_query.with_lockmode('update') \
            .update({
                'status': 'new',
                'started_at': None,
                'terminated_at': None
            }, synchronize_session='fetch')

    @classmethod
    def reset_status(cls, task_id, session=DBSession,
                     statuses=['in-progress']):
        session.query(RestfulpyTask) \
            .filter(RestfulpyTask.status.in_(statuses)) \
            .filter(RestfulpyTask.id == task_id) \
            .with_lockmode('update') \
            .update({
                'status': 'new',
                'started_at': None,
                'terminated_at': None
            }, synchronize_session='fetch')


def worker(statuses={'new'}, filters=None, tries=-1):
    isolated_session = create_thread_unsafe_session()
    context = {'counter': 0}
    tasks = []

    while True:
        context['counter'] += 1
        logger.debug("Trying to pop a task, Counter: %s" % context['counter'])
        try:
            task = RestfulpyTask.pop(
                statuses=statuses,
                filters=filters,
                session=isolated_session
            )
            assert task is not None

        except TaskPopError as ex:
            logger.debug('No task to pop: %s' % ex.to_json())
            isolated_session.rollback()
            if tries > -1:
                tries -= 1
                if tries <= 0:
                    return tasks
            time.sleep(settings.worker.gap)
            continue
        except:
            logger.exception('Error when popping task.')
            raise

        try:
            task.execute(context)

            # Task success
            task.status = 'success'
            task.terminated_at = datetime.utcnow()

        except:
            logger.exception('Error when executing task: %s' % task.id)
            task.status = 'failed'
            task.fail_reason = traceback.format_exc()[-4096:]

        finally:
            if isolated_session.is_active:
                isolated_session.commit()
            tasks.append((task.id, task.status))

