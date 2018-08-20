import threading

from restfulpy.taskqueue import RestfulpyTask, worker


awesome_task_done = threading.Event()
another_task_done = threading.Event()


class AwesomeTask(RestfulpyTask):

    __mapper_args__ = {
        'polymorphic_identity': 'awesome_task'
    }

    def do_(self, context):
        awesome_task_done.set()


class AnotherTask(RestfulpyTask):

    __mapper_args__ = {
        'polymorphic_identity': 'another_task'
    }

    def do_(self, context):
        another_task_done.set()


class BadTask(RestfulpyTask):

    __mapper_args__ = {
        'polymorphic_identity': 'bad_task'
    }

    def do_(self, context):
        raise Exception()


def test_worker(db):
    session = db()
    awesome_task = AwesomeTask()
    session.add(awesome_task)

    another_task = AnotherTask()
    session.add(another_task)

    bad_task = BadTask()
    session.add(bad_task)

    session.commit()

    tasks = worker(tries=0, filters=RestfulpyTask.type == 'awesome_task')
    assert len(tasks) == 1

    assert awesome_task_done.is_set() == True
    assert another_task_done.is_set() == False

    session.refresh(awesome_task)
    assert awesome_task.status == 'success'

    tasks = worker(tries=0, filters=RestfulpyTask.type == 'bad_task')
    assert len(tasks) == 1
    bad_task_id = tasks[0][0]
    session.refresh(bad_task)
    assert bad_task.status == 'failed'

    tasks = worker(tries=0, filters=RestfulpyTask.type == 'bad_task')
    assert len(tasks) == 0

    # Reset the status of one task
    session.refresh(bad_task)
    bad_task.status = 'in-progress'
    session.commit()
    session.refresh(bad_task)

    RestfulpyTask.reset_status(bad_task_id, session)
    session.commit()
    tasks = worker(tries=0, filters=RestfulpyTask.type == 'bad_task')
    assert len(tasks) == 1

    tasks = worker(tries=0, filters=RestfulpyTask.type == 'bad_task')
    assert len(tasks) == 0

    # Cleanup all tasks
    RestfulpyTask.cleanup(session, statuses=('in-progress', 'failed'))
    session.commit()

    tasks = worker(tries=0, filters=RestfulpyTask.type == 'bad_task')
    assert len(tasks) == 1

    tasks = worker(tries=0, filters=RestfulpyTask.type == 'bad_task')
    assert len(tasks) == 0

    # Doing all remaining tasks
    tasks = worker(tries=0)
    assert len(tasks) == 1


