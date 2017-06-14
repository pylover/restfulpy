from os import makedirs
from os.path import join, exists, dirname, basename
from urllib.parse import quote, urlencode
import warnings
from pprint import pprint

import ujson
from webtest import TestApp

from restfulpy.testing.constants import DOC_HEADER, DOC_LEGEND


class RequestSignature(object):
    def __init__(self, role, method, url, query_string=None, request_headers=None, response_headers=None):
        self.role = role
        self.method = method
        self.url = url
        self.query_string = query_string
        self.request_headers = request_headers
        self.response_headers = response_headers

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return hash((
            self.role, self.method, self.url, self.query_string,
            tuple(self.request_headers.items()) if self.request_headers else None,
            tuple(self.response_headers.items()) if self.response_headers else None
        ))


class FormParameter(object):
    def __init__(self, name, value=None, type_=str, optional=False, default=None):
        self.name = name
        self.type_ = type_
        self.optional = optional
        self.value = value
        self.default = default

    @property
    def type_string(self):
        if self.type_ is None:
            return ''
        return self.type_ if isinstance(self.type_, str) else self.type_.__name__

    @property
    def value_string(self):
        if self.value is None:
            return ''

        if self.type_ == 'file':
            return basename(self.value)

        if self.type_ is bool:
            return str(self.value).lower()

        return self.value

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return hash(self.name)


class DocumentaryTestApp(TestApp):
    _files = []
    _signatures = set()
    _jwt_token = None
    __jwt_header_key__ = 'HTTP_AUTHORIZATION'

    def __init__(self, destination_dir, application, *args, **kwargs):
        self.application = application
        self.destination_dir = destination_dir
        super(DocumentaryTestApp, self).__init__(application, *args, **kwargs)

    @property
    def legend_filename(self):
        return join(self.destination_dir, 'legend.md')

    @property
    def jwt_token(self):
        return self._jwt_token

    @jwt_token.setter
    def jwt_token(self, value):
        self._jwt_token = value

        if value is not None:
            self.extra_environ.update({
                self.__jwt_header_key__: value,
            })
        else:
            if self.__jwt_header_key__ in self.extra_environ:
                del self.extra_environ[self.__jwt_header_key__]

    def _ensure_file(self, filename, entity):
        d = dirname(filename)
        if not exists(d):
            makedirs(d)

        if not exists(self.legend_filename):
            with open(self.legend_filename, 'w') as f:
                f.write(DOC_LEGEND)

        if filename in self._files:
            return open(filename, 'a')
        else:
            f = open(filename, 'w')
            f.write(DOC_HEADER % dict(version=self.application.version))
            f.write('\n%s' % entity)
            f.write('\n%s\n' % ('=' * len(entity)))
            self._files.append(filename)
            return f

    def document(self, role, method, url, resp, request_headers, model=None, params=None, query_string=None,
                 url_params=None):
        signature = RequestSignature(
            role, method, url,
            query_string=tuple(query_string.keys()) if query_string else None,
            request_headers=request_headers,
            response_headers=resp.headers
        )
        if signature in self._signatures:
            return
        path_parts = url.split('?')[0].split('/')[1:]
        if len(path_parts) == 1:
            p = path_parts[0].strip()
            entity = filename = p if p else 'index'
        else:
            version, entity = path_parts[0:2]
            filename = '-'.join(path_parts[:2] + [method.lower()])

        filename = join(self.destination_dir, '%s.md' % filename)
        f = self._ensure_file(filename, entity)

        # Extracting more params & info from model if available
        if params and model:
            for c in model.iter_json_columns(relationships=False, include_readonly_columns=False):
                json_name = c.info.get('json', c.key)
                column = model.get_column(c)

                if hasattr(column, 'default') and column.default:
                    default_ = column.default.arg if column.default.is_scalar else 'function(...)'
                else:
                    default_ = ''

                type_ = column.type.python_type

                if json_name in params:
                    param = params[params.index(json_name)]
                    param.default = default_
                    if param.type_ is None:
                        param.type_ = type_
                    if param.optional is None:
                        param.optional = column.nullable
                else:
                    param = FormParameter(
                        json_name,
                        type_=type_,
                        optional=column.nullable,
                        default=default_)
                    params.append(param)

        try:
            f.write('## %s `%s`\n\n' % (method.upper(), url.replace('%(', '{').replace(')s', '}')))
            f.write('Role: %s\n\n' % role)

            if url_params:
                f.write('### Url Parameters:\n\n')
                f.write('| Parameter | Value |\n')
                f.write('| --------- | ----- |\n')
                for name, value in url_params.items():
                    f.write('| %s | %s |\n' % (name, value))

            if isinstance(params, dict):
                f.write('### Request: JSON\n\n')
                f.write('```json\n')
                pprint(params, stream=f, indent=8)
                f.write('```\n')

            elif isinstance(params, list):
                f.write('### Request: Form\n\n')
                f.write('| Parameter | Optional | Type | Default | Example |\n')
                f.write('| --------- | -------- | ---- | ------- | ------- |\n')
                for param in params:
                    f.write('| %s | %s | %s | %s | %s |\n' % (
                        param.name,
                        True if method.lower() == 'put' else param.optional,
                        param.type_string,
                        param.default if param.default is not None else '',
                        param.value_string))

            if query_string:
                f.write('### Query String:\n\n')

                f.write('| Parameter | Example |\n')
                f.write('| --------- | ------- |\n')
                for name, value in query_string.items():
                    f.write('| %s | %s |\n' % (
                        name,
                        str(value)))

            if request_headers:
                f.write('### Request Headers:\n\n')
                f.write('```\n')
                for k, v in request_headers.items():
                    f.write('%s: %s\n' % (k, v))
                f.write('```\n')
            f.write('\n\n')

            f.write('### Status:\n\n')
            f.write('`%s`\n\n' % resp.status)

            f.write('### Response Headers:\n\n')
            f.write('```\n')
            for k, v in resp.headers.items():
                f.write('%s: %s\n' % (k, v))
            f.write('```\n')

            f.write('### Response Body:\n\n')
            f.write('```json\n')
            if resp.charset in ('utf8', 'utf-8'):
                for l in resp.body.decode().splitlines():
                    f.write('%s\n' % l)
            else:
                f.write('%r\n' % resp.body)
            f.write('```\n\n')
            self._signatures.add(signature)
        finally:
            f.write('\n')
            f.close()

    def send_request(self, role, method, url, query_string=None, url_params=None,
                     params=None, model=None, doc=True, json=None, content_type=None, **kwargs):
        files = []

        parameters = {}
        if json:
            kwargs.setdefault('content_type', 'application/json')
            kwargs.update(
                params=ujson.dumps(json),
                upload_files=None,
            )

        else:
            kwargs.setdefault('content_type', content_type)
            if params:
                if isinstance(params, dict):
                    parameters = params
                    if doc:
                        warnings.warn(
                            'Skipping documentation generation, because the passed parameters are plain dict.',
                            stacklevel=4)
                        doc = False
                else:
                    for param in params:
                        if param.type_ == 'file':
                            files.append((param.name, param.value))
                        else:
                            parameters[param.name] = param.value

                if parameters:
                    kwargs['params'] = parameters

            if files:
                kwargs['upload_files'] = files

        real_url = (url % url_params) if url_params else url
        real_url = quote(real_url)

        if query_string:
            real_url = '%s?%s' % (real_url, urlencode(query_string))

        resp = self._gen_request(
            method.upper(), real_url, expect_errors=True, **kwargs
        )

        kwargs.setdefault('headers', {})
        content_type = kwargs.get('content_type', content_type)
        if content_type:
            kwargs['headers']['Content-Type'] = content_type

        if doc:
            self.document(role, method, url, resp, kwargs['headers'], model=model, params=json or params,
                          query_string=query_string, url_params=url_params)
        return resp
