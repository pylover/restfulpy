from os.path import abspath, exists, join, dirname

from appdirs import user_config_dir
from nanohttp import Controller

from restfulpy.orm import init_model, create_engine
from restfulpy.configuration import configure
from restfulpy.cli.main import MainLauncher


class Application:
    builtin_configuration = None

    def __init__(self, name: str, root: Controller, root_path='.', version='0.1.0-dev.0', process_name=None):
        self.process_name = process_name or name
        self.version = version
        self.root = root
        self.root_path = abspath(root_path)
        self.name = name
        self.cli_main = MainLauncher(self)

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

    def wsgi(self):
        return self.root.load_app()

    def insert_basedata(self):  # pragma: no cover
        raise NotImplementedError

    def insert_mockup(self):  # pragma: no cover
        raise NotImplementedError
