from urllib.parse import parse_qs
from os.path import join

import yaml


class Response:

    def __init__(self, status=None, headers=None):
        self.status = status
        self.headers = headers or []
        self.buffer = []

    def start_response_wrapper(self, start_response):
        def start_response_profiler(status, headers):
            self.status = status
            self.headers = headers
            return start_response(status, headers)
        return start_response_profiler

    def profile(self, wsgi_response):
        for chunk in wsgi_response:
            self.buffer.append(chunk)

    def dump(self):
        return dict(
            status=self.status,
            headers=self.headers,
            body=''.join(self.buffer)
        )


class ApiCall:
    response = None

    def __init__(self, application, environ, start_response):
        self.application = application
        self.environ = environ
        self.start_response = start_response
        self.response = Response()

    def __call__(self):
        self.response.profile(
            self.application(self.environ, self.response.start_response_wrapper(self.start_response))
        )

    @property
    def url(self):
        return self.environ['PATH_INFO']

    @property
    def title(self):
        return self.environ['TEST_CASE_TITLE']

    @property
    def verb(self):
        return self.environ['REQUEST_METHOD'].upper()

    @property
    def request(self):
        return self.environ['wsgi.input']

    @property
    def query_string(self):
        return {k: v[0] if len(v) == 1 else v for k, v in parse_qs(
            self.environ['QUERY_STRING'],
            keep_blank_values=True,
            strict_parsing=False
        ).items()}

    def to_dict(self):
        return dict(
            title=self.title,
            url=self.url,
            verb=self.verb,
            query_string=self.query_string,
            environ=self.environ,
            request=self.request,
            response=self.response.dump(),
        )

    def dump(self, file):
        yaml.dump(self.to_dict(), file)

    def save(self, directory):
        with open(join(directory, self.filename), '-w') as f:
            self.dump(f)

    @property
    def filename(self):
        url = self.url
        return f'{url}'


class AbstractDocumentaryMiddleware:

    def __init__(self, application):
        self.application = application

    def on_call_done(self, call):
        raise NotImplementedError()

    def __call__(self, environ, start_response):
        call = ApiCall(self.application, environ, start_response)
        call()
        self.on_call_done(call)
        for i in call.response.buffer:
            yield i


class FileDocumentaryMiddleware(AbstractDocumentaryMiddleware):

    def __init__(self, application, directory=None):
        super().__init__(application)
        self.directory = directory

    def on_call_done(self, call):
        call.save(self.directory)
