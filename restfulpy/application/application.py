import time
from os.path import abspath, join, dirname

from nanohttp import Application as NanohttpApplication, Controller, \
    HTTPStatus, HTTPInternalServerError, settings, context as nanohttp_context
from sqlalchemy.exc import SQLAlchemyError

from .. import logger
from ..configuration import configure
from ..exceptions import SQLError
from ..orm import init_model, create_engine, DBSession
from .cli.main import EntryPoint


class Application(NanohttpApplication):
    """The main entry point

    A web application project should be started by inheritting this class
    and overriding some methods if desirable

    """

    __configuration__ = None
    __authenticator__ = None
    __cli_arguments__ = []
    engine = None

    def __init__(self, name, root= None, path_='.', authenticator=None):
        super(Application, self).__init__(root=root)
        self.name = name
        self.path = abspath(path_)
        # TODO: rename to climain
        self.cli_main = EntryPoint(self).main

        if authenticator:
            self.__authenticator__ = authenticator

    def _handle_exception(self, ex, start_response):
        if isinstance(ex, SQLAlchemyError):
            ex = SQLError(ex)
            logger.error(ex)
        if not isinstance(ex, HTTPStatus):
            ex = HTTPInternalServerError('Internal server error')
            logger.error(ex)
        return super()._handle_exception(ex, start_response)

    def configure(self, filename=None, context=None, force=False):
        _context = {
            'appname': self.name,
            'dbname': self.name.lower(),
            'approot': self.path,
        }
        if context:
            _context.update(context)

        configure(context=_context, force=force)

        if self.__configuration__:
            settings.merge(self.__configuration__)

        if filename is not None:
            settings.loadfile(filename)

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

