from urllib.parse import parse_qs

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

    def __call__(self, environ, start_response):
        self.response.profile(
            self.application(self.environ, self.response.start_response_wrapper(start_response))
        )

    def dump(self):
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

    @property
    def filename(self):
        return f'{}'


class DocumentaryMiddleware:

    def __init__(self, application, directory=None):
        self.application = application
        self.directory = directory

    def __call__(self, environ, start_response):
        case = ApiCall(self.application, environ, start_response)
        case()
        case.save(join(self.directory, case.filename))
        for i in case.response.buffer:
            yield i

        result = case.run(self.application, start_response)
        with self.get_file(case) as file:
            case.dump(file)
        return result
