import collections
from os import path, makedirs

from .call import ApiCall


class AbstractDocumentaryMiddleware:

    def __init__(self, application, history_maxlen=50):
        self.application = application
        self.call_history = collections.deque(maxlen=history_maxlen)

    def on_call_done(self, call):
        raise NotImplementedError()

    def __call__(self, environ, start_response):
        call = ApiCall.from_environ(environ)

        response = self.application(
            environ,
            call.start_response_wrapper(start_response)
        )
        call.response.load(response)

        if not call.title.startswith('SKIP:'):
            self.call_history.append(call)
            self.on_call_done(call)
        for i in call.response.buffer:
            yield i


class FileDocumentaryMiddleware(AbstractDocumentaryMiddleware):

    def __init__(self, application, directory=None):
        super().__init__(application)
        directory = directory.rstrip('/')
        if not path.exists(directory):
            makedirs(directory, exist_ok=True)
        self.directory = directory

    def on_call_done(self, call):
        call.save(self.directory)
