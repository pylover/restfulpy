import threading

from restfulpy.taskqueue import Task, worker


awesome_task_done = threading.Event()
another_task_done = threading.Event()


class AwesomeTask(Task):

    __mapper_args__ = {
        'polymorphic_identity': 'awesome_task'
    }

    def do_(self, context):
        awesome_task_done.set()


class AnotherTask(Task):

    __mapper_args__ = {
        'polymorphic_identity': 'another_task'
    }

    def do_(self, context):
        another_task_done.set()


class BadTask(Task):

    __mapper_args__ = {
        'polymorphic_identity': 'bad_task'
    }

    def do_(self, context):
        raise Exception()


def test_worker(db):
    session = db()
    # noinspection PyArgumentList
    awesome_task = AwesomeTask()
    session.add(awesome_task)

    another_task = AnotherTask()
    session.add(another_task)

    bad_task = BadTask()
    session.add(bad_task)

    session.commit()

    tasks = worker(tries=0, filters=Task.type == 'awesome_task')
    assert len(tasks) == 1

    assert awesome_task_done.is_set() == True
    assert another_task_done.is_set() == False

    #TODO:remove these lines if tests passed
    #self.assertTrue(awesome_task_done.is_set())
    #self.assertFalse(another_task_done.is_set())

    session.refresh(awesome_task)
    assert awesome_task.status == 'success'

    tasks = worker(tries=0, filters=Task.type == 'bad_task')
    assert len(tasks) == 1
    bad_task_id = tasks[0][0]
    session.refresh(bad_task)
    assert bad_task.status == 'failed'

    tasks = worker(tries=0, filters=Task.type == 'bad_task')
    assert len(tasks) == 0

    # Reset the status of one task
    session.refresh(bad_task)
    bad_task.status = 'in-progress'
    session.commit()
    session.refresh(bad_task)

    Task.reset_status(bad_task_id, session)
    session.commit()
    tasks = worker(tries=0, filters=Task.type == 'bad_task')
    assert len(tasks) == 1

    tasks = worker(tries=0, filters=Task.type == 'bad_task')
    assert len(tasks) == 0

    # Cleanup all tasks
    Task.cleanup(session, statuses=('in-progress', 'failed'))
    session.commit()

    tasks = worker(tries=0, filters=Task.type == 'bad_task')
    assert len(tasks) == 1

    tasks = worker(tries=0, filters=Task.type == 'bad_task')
    assert len(tasks) == 0

    # Doing all remaining tasks
    tasks = worker(tries=0)
    assert len(tasks) == 1


