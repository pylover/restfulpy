
import unittest
import threading

from nanohttp import configure

from restfulpy.orm import init_model, create_engine, DBSession, setup_schema
from restfulpy.taskqueue import Task, worker
from restfulpy.testing import WebAppTestCase
from restfulpy.tests.helpers import MockupApplication


post_received = threading.Event()


class Post(Task):

    __mapper_args__ = {
        'polymorphic_identity': 'post'
    }

    def do_(self, context):  # pragma: no cover
        post_received.set()


class TaskQueueTestCase(WebAppTestCase):
    application = MockupApplication('MockupApplication', None)

    def test_worker(self):
        # noinspection PyArgumentList
        post1 = Post()
        DBSession.add(post1)
        DBSession.commit()
        self.assertEqual(post1.id, 1)

        worker(tries=0)
        self.assertTrue(post_received.is_set())


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
