import time

from restfulpy.application import Application


# noinspection PyAbstractClass
class MockupApplication(Application):
    builtin_configuration = '''
    db:
      test_uri: postgresql://postgres:postgres@localhost/restfulpy_test
      administrative_uri: postgresql://postgres:postgres@localhost/postgres      
    logging:
      loggers:
        default:
          level: critical
    '''

    def configure(self, files=None, context=None, **kwargs):
        _context = dict(
            process_name='restfulpy_unittests'
        )
        if context:
            _context.update(context)
        super().configure(files=files, context=_context, **kwargs)


class TimeMonkeyPatch:
    """
    For faking time
    """

    def __init__(self, fake_time):
        self.fake_time = fake_time

    def __enter__(self):
        self.real_time = time.time
        time.time = lambda: self.fake_time

    def __exit__(self, exc_type, exc_val, exc_tb):
        time.time = self.real_time
