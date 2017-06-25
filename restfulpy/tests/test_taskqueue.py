
import unittest
import threading

from nanohttp import configure

from restfulpy.orm import init_model, create_engine, DBSession, setup_schema
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
        post1 = AwesomeTask()
        self.session.add(post1)

        another_task1 = AnotherTask()
        self.session.add(another_task1)

        bad_task1 = BadTask()
        self.session.add(bad_task1)

        self.session.commit()

        tasks = worker(tries=0, filters=Task.type == 'awesome_task')
        self.assertEqual(len(tasks), 1)
        self.assertTrue(awesome_task_done.is_set())
        self.assertFalse(another_task_done.is_set())

        tasks = worker(tries=0, filters=Task.type == 'bad_task')
        self.assertEqual(len(tasks), 1)
        bad_task_id = tasks[0][0]

        tasks = worker(tries=0, filters=Task.type == 'bad_task')
        self.assertEqual(len(tasks), 0)

        # Reset the status of one task
        Task.reset_status(bad_task_id, self.session)
        self.session.commit()
        tasks = worker(tries=0, filters=Task.type == 'bad_task')
        self.assertEqual(len(tasks), 1)

        tasks = worker(tries=0, filters=Task.type == 'bad_task')
        self.assertEqual(len(tasks), 0)

        # Cleanup all tasks
        Task.cleanup(self.session)
        self.session.commit()

        tasks = worker(tries=0, filters=Task.type == 'bad_task')
        self.assertEqual(len(tasks), 1)

        tasks = worker(tries=0, filters=Task.type == 'bad_task')
        self.assertEqual(len(tasks), 0)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
