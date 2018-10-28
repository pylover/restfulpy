import time
from os.path import abspath, exists, join, dirname

from appdirs import user_config_dir
from sqlalchemy.exc import SQLAlchemyError

from nanohttp import Application as NanohttpApplication, Controller, \
    HTTPStatus, HTTPInternalServerError, settings, context as nanohttp_context
from .cli.main import MainLauncher
from ..authentication import Authenticator
from ..configuration import configure
from ..exceptions import SqlError
from ..logging_ import get_logger
from ..orm import init_model, create_engine, DBSession


class Application(NanohttpApplication):
    """The main entry point

    A web application project should be started by inheritting this class
    and overriding some methods if desirable

    """

    __configuration__ = None
    __logger__ = get_logger()
    __authenticator__ = None
    __configuration_cipher__ = None
    engine = None

    def __init__(self, name: str, root: Controller, root_path='.',
                 version='0.1.0-dev.0', process_name=None, authenticator=None,
                 configuration=None):
        super(Application, self).__init__(root=root)
        self.process_name = process_name or name
        self.version = version
        self.root_path = abspath(root_path)
        self.name = name
        self.cli_main = MainLauncher(self)

        if configuration:
            self.__configuration__ = configuration

        if authenticator:
            self.__authenticator__ = authenticator

    def _handle_exception(self, ex, start_response):
        if isinstance(ex, SQLAlchemyError):
            ex = SqlError(ex)
            self.__logger__.exception(str(ex))
        if not isinstance(ex, HTTPStatus):
            ex = HTTPInternalServerError('Internal server error')
            self.__logger__.exception('Internal server error')
        return super()._handle_exception(ex, start_response)

    def configure(self, files=None, context=None, force=False):
        _context = {
            'process_name': self.process_name,
            'root_path': self.root_path,
            'data_dir': join(self.root_path, 'data'),
            'restfulpy_dir': abspath(dirname(__file__))
        }
        if context:
            _context.update(context)

        configure(context=_context, force=force)
        settings.merge(self.__configuration__)

        files = ([files] if isinstance(files, str) else files) or []
        local_config_file = join(user_config_dir(), '%s.yml' % self.name)
        if exists(local_config_file):  # pragma: no cover
            files.insert(0, local_config_file)

        for filename in files:
            with open(filename, 'rb') as f:
                header = f.read(4)
                if header == b'#enc':
                    content = self.__configuration_cipher__.decrypt(f.read())
                else:
                    content = header + f.read()
                settings.merge(content.decode())

    def register_cli_launchers(self, subparsers):
        """
        This is a template method
        """
        pass

    def initialize_orm(self, engine=None):
        if engine is None:
            engine = create_engine()

        self.engine = engine
        init_model(engine)

    # Hooks
    def begin_request(self):
        if self.__authenticator__:
            self.__authenticator__.authenticate_request()

    def begin_response(self):
        if settings.timestamp:
            nanohttp_context.response_headers.add_header(
                'X-Server-Timestamp',
                str(time.time())
            )

    def end_response(self):
        DBSession.remove()

    def insert_basedata(self):  # pragma: no cover
        raise NotImplementedError()

    def insert_mockup(self):  # pragma: no cover
        raise NotImplementedError()

    def shutdown(self):
        DBSession.close_all()
        self.engine.dispose()

