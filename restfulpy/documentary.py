from urllib.parse import parse_qs

import yaml


class ApiTestCase:
    response = None

    def __init__(self, environ):
        self.environ = environ

    def run(self, application, start_response):
        def _start_response(status, headers):
            start_response(status, headers)
        self.response = application(self.environ, _start_response)
        return self.response

    def to_dict(self):
        return dict(
            title=self.title,
            url=self.url,
            verb=self.verb,
            query_string=self.query_string,
            environ=self.environ,
            request=self.request,
            response=self.response,
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


class DocumentaryMiddleware:

    def __init__(self, application):
        self.application = application

    def get_file(self, case):
        raise NotImplementedError()

    def __call__(self, environ, start_response):
        case = ApiTestCase(environ)
        result = case.run(self.application, start_response)
        with self.get_file(case) as file:
            case.dump(file)
        return result
