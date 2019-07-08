import time
from datetime import datetime

from nanohttp import settings
from sqlalchemy import Integer, Enum, Unicode, DateTime, or_, and_
from sqlalchemy.sql.expression import text

from . import logger
from .exceptions import RestfulException
from .orm import TimestampMixin, DeclarativeBase, Field, DBSession, \
    create_thread_unsafe_session


class TaskPopError(RestfulException):
    pass


class MuleTask(TimestampMixin, DeclarativeBase):
    __tablename__ = 'mule_task'

    id = Field(Integer, primary_key=True, json='id')
    at = Field(DateTime, nullable=True, json='at', default=datetime.now)
    status = Field(
        Enum(
            'new',
            'in-progress',
            'expired',
            'success',
            'failed',

            name='mule_status_enum'
        ),
        default='new',
        nullable=True, json='status'
    )
    expired_at = Field(DateTime, nullable=True, json='expiredAt')
    terminated_at = Field(DateTime, nullable=True, json='terminatedAt')
    type = Field(Unicode(50))

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'polymorphic_on': type
    }

    def do_(self):
        raise NotImplementedError

    @classmethod
    def pop(cls, statuses={'new'}, filters=None, session=DBSession):

        find_query = session.query(
            cls.id.label('id'),
            cls.created_at,
            cls.at,
            cls.status,
        )
        if filters is not None:
            find_query = find_query.filter(
                text(filters) if isinstance(filters, str) else filters
            )

        find_query = find_query \
            .filter(cls.at <= datetime.now()) \
            .filter(
                or_(
                    cls.status == 'in-progress', cls.status == 'new', \
                    and_(
                        cls.status == 'failed',
                        cls.expired_at > datetime.now()
                    )
                )
            ) \
            .limit(1) \
            .with_for_update()

        cte = find_query.cte('find_query')
        update_query = MuleTask.__table__.update() \
            .where(MuleTask.id == cte.c.id) \
            .values(status='in-progress') \
            .returning(MuleTask.__table__.c.id)

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
                .query(MuleTask) \
                .filter(MuleTask.id == self.id) \
                .one()
            isolated_task.do_(context)
            session.commit()
        except:
            session.rollback()
            raise


def worker(statuses={'new'},filters=None, tries=-1):
    isolated_session = create_thread_unsafe_session()
    context = {'counter': 0}
    tasks = []

    while True:
        context['counter'] += 1
        logger.debug('Trying to pop a task, Counter: %s' % context['counter'])
        try:
            task = MuleTask.pop(
                statuses=statuses,
                filters=filters,
                session=isolated_session
            )

        except TaskPopError as ex:
            logger.debug('No task to pop: %s' % ex.to_json())
            isolated_session.rollback()
            if tries > -1:
                tries -= 1
                if tries <= 0:
                    return tasks
            time.sleep(settings.jobs.interval)
            continue

        try:
            task.execute(context)

            # Task success
            task.status = 'success'
            task.terminated_at = datetime.utcnow()

        except:
            logger.error('Error when executing task: %s' % task.id)
            task.status = 'failed'

        finally:
            if isolated_session.is_active:
                isolated_session.commit()
            tasks.append((task.id, task.status))

