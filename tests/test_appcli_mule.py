import time

from bddcli import Given, stderr, Application, status, when, story, \
    given

from restfulpy import Application as RestfulpyApplication
from restfulpy.mule import MuleTask


DBURL = 'postgresql://postgres:postgres@localhost/restfulpy_test'


class WorkerTask(MuleTask):

    __mapper_args__ = {
        'polymorphic_identity': 'worker_task'
    }

    def do_(self, context):
        _task_done.set()


class FooApplication(RestfulpyApplication):
    __configuration__ = f'''
      db:
        url: {DBURL}
    '''


foo = FooApplication(name='Foo')


def foo_main():
    return foo.cli_main()


app = Application('foo', 'tests.test_appcli_mule:foo_main')


def test_appcli_mule_start(db):
    session = db()
    task = WorkerTask()
    session.add(task)
    session.commit()

    with Given(app, 'mule start', nowait=True):
        time.sleep(2)
        story.kill()
        story.wait()
        assert status == -15

        when(given + '--query-interval 1')
        time.sleep(2)
        story.kill()
        story.wait()
        assert status == -15


if __name__ == '__main__':  # pragma: no cover
    foo.cli_main(['mule', '--help'])

