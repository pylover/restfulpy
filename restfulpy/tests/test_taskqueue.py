
import unittest
import threading

from restfulpy.taskqueue import Task, worker
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication


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


class TaskQueueTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', None)

    def test_worker(self):
        # noinspection PyArgumentList
        awesome_task = AwesomeTask()
        self.session.add(awesome_task)

        another_task = AnotherTask()
        self.session.add(another_task)

        bad_task = BadTask()
        self.session.add(bad_task)

        self.session.commit()

        tasks = worker(tries=0, filters=Task.type == 'awesome_task')
        self.assertEqual(len(tasks), 1)
        self.assertTrue(awesome_task_done.is_set())
        self.assertFalse(another_task_done.is_set())

        self.session.refresh(awesome_task)
        self.assertEqual(awesome_task.status, 'success')

        tasks = worker(tries=0, filters=Task.type == 'bad_task')
        self.assertEqual(len(tasks), 1)
        bad_task_id = tasks[0][0]
        self.session.refresh(bad_task)
        self.assertEqual(bad_task.status, 'failed')

        tasks = worker(tries=0, filters=Task.type == 'bad_task')
        self.assertEqual(len(tasks), 0)

        # Reset the status of one task
        self.session.refresh(bad_task)
        bad_task.status = 'in-progress'
        self.session.commit()
        self.session.refresh(bad_task)

        Task.reset_status(bad_task_id, self.session)
        self.session.commit()
        tasks = worker(tries=0, filters=Task.type == 'bad_task')
        self.assertEqual(len(tasks), 1)

        tasks = worker(tries=0, filters=Task.type == 'bad_task')
        self.assertEqual(len(tasks), 0)

        # Cleanup all tasks
        Task.cleanup(self.session, statuses=('in-progress', 'failed'))
        self.session.commit()

        tasks = worker(tries=0, filters=Task.type == 'bad_task')
        self.assertEqual(len(tasks), 1)

        tasks = worker(tries=0, filters=Task.type == 'bad_task')
        self.assertEqual(len(tasks), 0)

        # Doing all remaining tasks
        tasks = worker(tries=0)
        self.assertEqual(len(tasks), 1)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
