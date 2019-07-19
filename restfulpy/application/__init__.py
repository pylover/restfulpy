import time
from os.path import abspath, exists, join, dirname

from sqlalchemy.exc import SQLAlchemyError

from nanohttp import Application as NanohttpApplication, Controller, \
    HTTPStatus, HTTPInternalServerError, settings, context as nanohttp_context
from .cli.main import EntryPoint
from ..authentication import Authenticator
from ..configuration import configure
from ..exceptions import SqlError
from ..orm import init_model, create_engine, DBSession
from ..cryptography import AESCipher
from .. import logger


class Application(NanohttpApplication):
    """The main entry point

    A web application project should be started by inheritting this class
    and overriding some methods if desirable

    """

    __configuration__ = None
    __authenticator__ = None
    __configuration_cipher__ = AESCipher(b'abcdefghijklmnop')
    engine = None

    def __init__(self, name: str, root: Controller = None, root_path='.',
                 version='0.1.0a0', process_name=None, authenticator=None):
        super(Application, self).__init__(root=root)
        self.process_name = process_name or name
        self.version = version
        self.root_path = abspath(root_path)
        self.name = name
        self.cli_main = EntryPoint(self).main

        if authenticator:
            self.__authenticator__ = authenticator

    def _handle_exception(self, ex, start_response):
        if isinstance(ex, SQLAlchemyError):
            ex = SqlError(ex)
            logger.error(ex)
        if not isinstance(ex, HTTPStatus):
            ex = HTTPInternalServerError('Internal server error')
            logger.error(ex)
        return super()._handle_exception(ex, start_response)

    def configure(self, filename=None, context=None, force=False):
        _context = {
            'process_name': self.process_name,
            'root_path': self.root_path,
            'data_dir': join(self.root_path, 'data'),
            'restfulpy_dir': abspath(dirname(__file__))
        }
        if context:
            _context.update(context)

        configure(context=_context, force=force)

        if self.__configuration__:
            settings.merge(self.__configuration__)

        if filename is not None:
            with open(filename, 'rb') as f:
                header = f.read(4)
                if header == b'#enc':
                    content = self.__configuration_cipher__.decrypt(f.read())
                else:
                    content = header + f.read()
                settings.merge(content.decode())

    def get_cli_arguments(self):
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

    def insert_basedata(self, args=None):
        raise NotImplementedError()

    def insert_mockup(self, args=None):
        raise NotImplementedError()

