import threading
import datetime

from restfulpy.mule import MuleTask, worker
from freezegun import freeze_time


awesome_task_done = threading.Event()
another_task_done = threading.Event()

class AwesomeTask(MuleTask):

    __mapper_args__ = {
        'polymorphic_identity': 'awesome_task'
    }
    def do_(self, context):
        awesome_task_done.set()


class AnotherTask(MuleTask):

    __mapper_args__ = {
        'polymorphic_identity': 'another_task'
    }

    def do_(self, context):
        another_task_done.set()


class BadTask(MuleTask):

    __mapper_args__ = {
        'polymorphic_identity': 'bad_task'
    }

    def do_(self, context):
        raise Exception()


def test_worker(db):
    session = db()
    awesome_task = AwesomeTask()
    session.add(awesome_task)

    another_task = AnotherTask(
        at = datetime.date.today() + datetime.timedelta(days=1)
    )
    session.add(another_task)

    bad_task = BadTask(
        at = datetime.date.today() + datetime.timedelta(days=1)
    )
    session.add(bad_task)

    session.commit()

    tasks = worker(tries=0, filters=MuleTask.type == 'awesome_task')
    assert len(tasks) == 1

    assert awesome_task_done.is_set() == True

    session.refresh(awesome_task)
    assert awesome_task.status == 'success'

    tasks = worker(tries=0, filters=MuleTask.type == 'another_task')
    assert len(tasks) == 0

    assert another_task_done.is_set() == False

    aa = datetime.date.today() + datetime.timedelta(days=2)
    with freeze_time(datetime.date.today() + datetime.timedelta(days=2)):
        tasks = worker(tries=0, filters=MuleTask.type == 'bad_task')
        assert len(tasks) == 1
        #bad_task_id = tasks[0][0]
        session.refresh(bad_task)
        assert bad_task.status == 'failed'

    tasks = worker(tries=0, filters=MuleTask.type == 'bad_task')
    assert len(tasks) == 0

