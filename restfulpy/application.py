
from os.path import abspath, exists, join, dirname

from appdirs import user_config_dir
from nanohttp import Application as NanohttpApplication, Controller, settings, context, HttpStatus, HttpInternalServerError

from restfulpy.orm import init_model, create_engine, DBSession
from restfulpy.configuration import configure
from restfulpy.cli.main import MainLauncher
from restfulpy.logging_ import get_logger
from restfulpy.authentication import Authenticator


class Application(NanohttpApplication):
    builtin_configuration = None
    __logger__ = get_logger()
    __authenticator__ = None

    def __init__(self, name: str, root: Controller, root_path='.', version='0.1.0-dev.0', process_name=None,
                 authenticator=None):
        super(Application, self).__init__(root=root)
        self.process_name = process_name or name
        self.version = version
        self.root_path = abspath(root_path)
        self.name = name
        self.cli_main = MainLauncher(self)
        if authenticator:
            self.__authenticator__ = authenticator
        elif self.__authenticator__ is None:
            self.__authenticator__ = Authenticator()

    def _handle_exception(self, ex):
        if not isinstance(ex, HttpStatus):
            ex = HttpInternalServerError('Internal server error')
            self.__logger__.exception('Internal server error')
        return super()._handle_exception(ex)

    def configure(self, files=None, context=None, **kwargs):
        _context = {
            'process_name': self.process_name,
            'root_path': self.root_path,
            'data_dir': join(self.root_path, 'data'),
            'restfulpy_dir': abspath(dirname(__file__))
        }
        if context:
            _context.update(context)

        files = files or []
        if isinstance(files, str):
            files = [files]
        local_config_file = join(user_config_dir(), '%s.yml' % self.name)
        if exists(local_config_file):  # pragma: no cover
            print('Gathering config file: %s' % local_config_file)
            files.insert(0, local_config_file)

        configure(config=self.builtin_configuration, files=files, context=_context, **kwargs)

    # noinspection PyMethodMayBeStatic
    def register_cli_launchers(self, subparsers):
        """
        This is a template method
        """
        pass

    @classmethod
    def initialize_models(cls):
        init_model(create_engine())
        
    # Hooks
    def begin_request(self):
        self.__authenticator__.authenticate_request()

    # noinspection PyMethodMayBeStatic
    def begin_response(self):
        if settings.debug:
            context.response_headers.add_header('Access-Control-Allow-Origin', 'http://localhost:8080')
            context.response_headers.add_header('Access-Control-Allow-Methods',
                                                'GET, POST, PUT, DELETE, UNDELETE, METADATA, PATCH, SEARCH')
            context.response_headers.add_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, '
                                                                                'X-HTTP-Verb')
            context.response_headers.add_header('Access-Control-Expose-Headers',
                                                'Content-Type, X-Pagination-Count, X-Pagination-Skip, '
                                                'X-Pagination-Take, X-New-JWT-Token')
            context.response_headers.add_header('Access-Control-Allow-Credentials', 'true')

    # noinspection PyMethodMayBeStatic
    def end_response(self):
        DBSession.remove()

    def insert_basedata(self):  # pragma: no cover
        raise NotImplementedError

    def insert_mockup(self):  # pragma: no cover
        raise NotImplementedError
