
import ujson
import unittest
from os import makedirs
from os.path import join, exists, dirname, basename, abspath
from urllib.parse import quote

from webtest import TestApp
from nanohttp import settings

from restfulpy.db import DatabaseManager
from restfulpy.messaging import Messenger
from restfulpy.orm import setup_schema, create_engine, session_factory, DBSession


class As:
    visitor = 'Visitor'
    logged_in = 'LoggedIn'
    supervisor = 'Supervisor'
    everyone = '%s|%s|%s' % (visitor, logged_in, supervisor)


class RequestSignature(object):
    def __init__(self, role, method, url, query_string=None):
        self.role = role
        self.method = method
        self.url = url
        self.query_string = query_string

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __hash__(self):
        return hash((self.role, self.method, self.url, self.query_string))


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

    def __init__(self, destination_dir, application, *args, **kwargs):
        self.application = application
        self.destination_dir = destination_dir
        super(DocumentaryTestApp, self).__init__(application.wsgi(), *args, **kwargs)

    _header = """
[Author]: <TestEngine>
[Version]: <%(version)s>
[Status]: <Implemented>

Legend
======

Paging
======

| Param  | Meaning            |
| ------ | ------------------ |
| limit  | Rows per page      |
| offset | Skip N rows        |


Search & Filtering
==================

You can search and filter the result via query-string:

        /path/to/resource?field=[op]value

| Operator  | Meaning |
| --------- | ------- |
|           | =       |
| !         | !=      |
| >         | >       |
| >=        | >=      |
| <         | <       |
| <=        | <=      |
| %%        | LIKE    |
| ^         | IN      |
| !^        | NOT IN  |


Sorting
=======

You can sort like this:


        /path/to/resource?sort=[op]value


| Operator  | Meaning |
| --------- | ------- |
|           | ASC     |
| \-        | DESC    |


"""

    def _ensure_file(self, filename, entity):
        if filename in self._files:
            return open(filename, 'a')
        else:
            d = dirname(filename)
            if not exists(d):
                makedirs(d)
            f = open(filename, 'w')
            f.write(self._header % dict(version=self.application.version))
            f.write('\n%s' % entity)
            f.write('\n%s\n' % ('-' * len(entity)))
            self._files.append(filename)
            return f

    def document(self, role, method, url, resp, model=None, params=None, query_string=None):
        signature = RequestSignature(role, method, url, tuple(query_string.keys()) if query_string else None)
        if signature in self._signatures:
            return
        path_parts = url.split('?')[0].split('/')[1:]
        if len(path_parts) == 1:
            p = path_parts[0].strip()
            entity = filename = p if p else 'index'
        else:
            version, entity = path_parts[0:2]
            filename = '_'.join(path_parts[:2] + [method.lower()])

        filename = join(self.destination_dir, '%s.md' % filename)
        f = self._ensure_file(filename, entity)

        # Extracting more params & info from model if available
        if params and model:
            for c in model.iter_json_columns(relationships=False, include_readonly_columns=False):
                json_name = c.info['json']
                column = model.get_column(c)

                if hasattr(column, 'default') and column.default:
                    default_ = column.default.arg if column.default.is_scalar else 'function(...)'
                else:
                    default_ = ''

                if 'attachment' in column.info:
                    type_ = 'attachment'
                else:
                    type_ = str if 'unreadable' in column.info and column.info['unreadable'] else \
                        column.type.python_type

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
            f.write('\n- (%s) **%s** `%s`\n' % (role, method.upper(), url))
            if params:
                f.write('\n    - Form Parameters:\n\n')
                f.write('        | Parameter | Optional | Type | Default | Example |\n')
                f.write('        | --------- | -------- | ---- | ------- | ------- |\n')
                for param in params:
                    f.write('        | %s | %s | %s | %s | %s |\n' % (
                        param.name,
                        True if method.lower() == 'put' else param.optional,
                        param.type_string,
                        param.default if param.default is not None else '',
                        param.value_string))
            if query_string:
                f.write('\n    - Query String:\n\n')
                f.write('        | Parameter | Example |\n')
                f.write('        | --------- | ------- |\n')
                for name, value in query_string.items():
                    f.write('        | %s | %s |\n' % (
                        name,
                        str(value)))

            f.write('\n    - Response:\n\n')
            for l in resp.body.decode().splitlines():
                f.write('%s%s\n' % (12 * ' ', l))
            f.write('\n\n')
            self._signatures.add(signature)
        finally:
            f.close()

    def send_request(self, role, method, url, query_string=None, url_params=None,
                     params=None, model=None, doc=True, **kwargs):
        files = []
        parameters = {}
        if params:
            for param in params:
                if param.type_ == 'file':
                    files.append((param.name, param.value))
                else:
                    parameters[param.name] = param.value

        if query_string:
            parameters.update(query_string)

        if files:
            kwargs['upload_files'] = files
        if parameters:
            kwargs['params'] = parameters

        real_url = (url % url_params) if url_params else url
        real_url = quote(real_url)
        kwargs['expect_errors'] = True
        resp = getattr(self, method.lower())(real_url, **kwargs)

        if doc:
            self.document(role, method, url, resp, model=model, params=params, query_string=query_string)
        return resp

    def metadata(self, url, params='', headers=None, extra_environ=None,
                 status=None, upload_files=None, expect_errors=False,
                 content_type=None, xhr=False):
        if xhr:
            headers = self._add_xhr_header(headers)
        return self._gen_request('METADATA', url, params=params, headers=headers,
                                 extra_environ=extra_environ, status=status,
                                 upload_files=upload_files,
                                 expect_errors=expect_errors,
                                 content_type=content_type,
                                 )

    def undelete(self, url, params='', headers=None, extra_environ=None,
                 status=None, upload_files=None, expect_errors=False,
                 content_type=None, xhr=False):
        if xhr:
            headers = self._add_xhr_header(headers)
        return self._gen_request('UNDELETE', url, params=params, headers=headers,
                                 extra_environ=extra_environ, status=status,
                                 upload_files=upload_files,
                                 expect_errors=expect_errors,
                                 content_type=content_type,
                                 )


class WebAppTestCase(unittest.TestCase):
    config = None
    application = None
    db_name = None

    @classmethod
    def prepare_database(cls):
        with DatabaseManager() as m:
            m.drop_database()
            m.create_database()

        engine = create_engine()
        session = session_factory(bind=engine)
        setup_schema(session)
        session.commit()
        session.close_all()
        engine.dispose()

    @classmethod
    def drop_database(cls):
        DBSession.close_all()
        if DBSession.bind and hasattr(DBSession.bind, 'dispose'):
            DBSession.bind.dispose()
        with DatabaseManager() as m:
            m.drop_database()

    @classmethod
    def setUpClass(cls):
        cls.application.configure(config=cls.config, force=True)
        cls.prepare_database()
        cls.application.insert_basedata()
        cls.application.insert_mockup()
        cls.wsgi_app = DocumentaryTestApp(
            abspath(join(settings.api_documents.directory, 'api')),
            cls.application
        )

    @classmethod
    def tearDownClass(cls):
        cls.drop_database()

    def login(self, username, password):
        result, metadata = self.request(None, '/login', params={
            'username': username,
            'password': password
        })
        self.wsgi_app.jwt_token = result['token']

    def logout(self):
        self.wsgi_app.jwt_token = ''

    def request(self, *args, expected_status=200, expected_headers=None, **kwargs):
        resp = self.wsgi_app.send_request(*args, **kwargs)

        if resp.status_code != expected_status:
            print('#' * 80)
            print(resp.text)
            print('#' * 80)

        self.assertEqual(resp.status_code, expected_status)

        if expected_headers:
            for k, v in expected_headers.items():
                self.assertIn(k, resp.headers)
                self.assertEqual(v, resp.headers[k])

        if 'content-type' in resp.headers and resp.headers['content-type'].startswith('application/json'):
            result = ujson.loads(resp.body.decode())
        else:
            result = resp.body

        return result, None


class ModelRestCrudTestCase(WebAppTestCase):
    __model__ = None

    def request(self, *args, model=None, **kwargs):
        return super(ModelRestCrudTestCase, self).request(
            *args,
            model=self.__model__,
            **kwargs
        )


class DeferredBaseMessenger(object):
    _last_body = None

    @property
    def last_body(self):
        return self.__class__._last_body

    @last_body.setter
    def last_body(self, value):
        self.__class__._last_body = value


class MockupMessenger(Messenger, DeferredBaseMessenger):

    def send_from(self, from_, to, subject, body, cc=None, bcc=None, template_string=None, template_filename=None):
        self.last_body = {
            'to': to,
            'body': body,
            'subject': subject
        }
