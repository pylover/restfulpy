
import time
import argparse
import threading
from os import remove
import tempfile
from os.path import dirname, abspath, join, exists
from subprocess import run
from wsgiref.simple_server import make_server

from sqlalchemy import Integer, Unicode
from nanohttp import text, json, context, RestController, HttpBadRequest, etag, HttpNotFound
from restfulpy.authorization import authorize
from restfulpy.application import Application
from restfulpy.authentication import StatefulAuthenticator
from restfulpy.controllers import RootController, ModelRestController, JsonPatchControllerMixin
from restfulpy.orm import DeclarativeBase, OrderingMixin, PaginationMixin, FilteringMixin, Field, setup_schema, \
    DBSession, ModifiedMixin, commit
from restfulpy.principal import JwtPrincipal, JwtRefreshToken
from restfulpy.cli import Launcher
from restfulpy.templating import template


__version__ = '0.1.1'


here = abspath(dirname(__file__))
db = abspath(join(tempfile.gettempdir(), 'restfulpy-mockup-server.sqlite'))


class MockupMember:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class Resource(ModifiedMixin, OrderingMixin, PaginationMixin, FilteringMixin, DeclarativeBase):
    __tablename__ = 'resource'

    id = Field(Integer, primary_key=True)
    title = Field(
        Unicode(30),
        watermark='title here',
        icon='default',
        label='Title',
        pattern='[a-zA-Z0-9]{3,}',
        min_length=3
    )

    @property
    def __etag__(self):
        return self.last_modification_time.isoformat()


class MockupAuthenticator(StatefulAuthenticator):
    def validate_credentials(self, credentials):
        email, password = credentials
        if email == 'user1@example.com' and password == '123456':
            return MockupMember(id=1, email=email, roles=['user'])

    def create_refresh_principal(self, member_id=None):
        return JwtRefreshToken(dict(id=member_id))

    def create_principal(self, member_id=None, session_id=None):
        return JwtPrincipal(dict(id=1, email='user1@example.com', roles=['user'], sessionId='1'))


class AuthController(RestController):

    @json
    def post(self):
        email = context.form.get('email')
        password = context.form.get('password')

        def bad():
            raise HttpBadRequest('Invalid email or password')

        if not (email and password):
            bad()

        principal = context.application.__authenticator__.login((email, password))
        if principal is None:
            bad()

        return dict(token=principal.dump())

    @json
    def delete(self):
        return {}


class ResourceController(JsonPatchControllerMixin, ModelRestController):
    __model__ = Resource

    @json
    @etag
    @Resource.expose
    def get(self, id_: int=None):
        q = Resource.query
        if id_ is not None:
            return q.filter(Resource.id == id_).one_or_none()
        return q

    @json
    @etag
    @Resource.expose
    @commit
    def put(self, id_: int=None):
        m = Resource.query.filter(Resource.id == id_).one_or_none()
        if m is None:
            raise HttpNotFound()
        m.update_from_request()
        context.etag_match(m.__etag__)
        return m

    @json
    @etag
    @commit
    def post(self):
        m = Resource()
        m.update_from_request()
        DBSession.add(m)
        return m

    @json
    @etag
    @commit
    def delete(self, id_: int=None):
        m = Resource.query.filter(Resource.id == id_).one_or_none()
        context.etag_match(m.__etag__)
        DBSession.delete(m)
        return m


class Root(RootController):
    resources = ResourceController()
    sessions = AuthController()

    @template('help.mako')
    def index(self):
        return dict(url=f'http://{context.environ["HTTP_HOST"]}')

    @json
    def echo(self):
        return {k: v for i in (context.form, context.query_string) for k, v in i.items()}

    @text
    @authorize
    def protected(self):
        return 'Protected'

    @json
    def version(self):
        return {
            'version': __version__
        }


class MockupApplication(Application):
    __authenticator__ = MockupAuthenticator()
    builtin_configuration = f'''
    debug: true
    
    db:
      url: sqlite:///{db}
      
    jwt:
      max_age: 20
      refresh_token:
        max_age: 60
        secure: false
    
    templates:
      directories:
        - {here}/templates    
    '''

    def __init__(self):
        super().__init__(
            'restfulpy-client-js-mockup-server',
            root=Root(),
            version=__version__,
        )

    def insert_basedata(self):
        pass

    def insert_mockup(self):
        for i in range(1, 11):
            # noinspection PyArgumentList
            DBSession.add(Resource(id=i, title='resource%s' % i))
        DBSession.commit()

    def begin_request(self):
        if 'HTTP_ORIGIN' in context.environ:
            context.response_headers.add_header('Access-Control-Allow-Origin', context.environ['HTTP_ORIGIN'])
        super(MockupApplication, self).begin_request()


class SimpleMockupServerLauncher(Launcher):
    __command__ = 'mockup-server'
    default_bind = '8080'
    application = None

    @classmethod
    def create_parser(cls, subparsers):
        parser = subparsers.add_parser(cls.__command__, help='Starts the mockup http server.')
        parser.add_argument(
            '-c', '--config-file',
            metavar="FILE",
            help='List of configuration files separated by space. Default: ""'
        )
        parser.add_argument(
            '-b', '--bind',
            default=cls.default_bind,
            metavar='{HOST:}PORT',
            help=f'Bind Address. default is {cls.default_bind}, A free tcp port will be choosed automatically if the '
                 f'0 (zero) is given'
        )

        parser.add_argument(
            'command',
            nargs=argparse.REMAINDER,
            default=[],
            help='The command to run tests.'
        )

        parser.add_argument('-v', '--version', action='store_true', help='Show the mockup server\'s version.')
        return parser

    def launch(self):
        if self.args.version:
            print(__version__)
            return

        self.application = MockupApplication()
        self.application.configure(files=self.args.config_file)
        if exists(db):
            remove(db)
        # makedirs(settings.data_directory, exist_ok=True)
        self.application.initialize_models()
        setup_schema()
        # DBSession.commit()
        print(f'DB {DBSession.bind}')
        self.application.insert_mockup()
        host, port = self.args.bind.split(':') if ':' in self.args.bind else ('localhost', self.args.bind)
        httpd = make_server(host, int(port), self.application)

        url = 'http://%s:%d' % httpd.server_address
        print(f'The server is up!, Get {url} to more info about how to use it!')
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        try:
            server_thread.start()

            if not self.args.command:
                server_thread.join()
            else:
                test_runner_command = ' '.join(self.args.command).replace('{url}', url)
                time.sleep(1)
                run(test_runner_command, shell=True)
            return 0
        except KeyboardInterrupt:
            print('CTRL+X is pressed.')
            return 1
        finally:
            httpd.shutdown()
            server_thread.join()
