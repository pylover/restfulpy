
from os.path import abspath, exists, join, dirname

from appdirs import user_config_dir
from nanohttp import Controller

from restfulpy.cli.main import MainLauncher
from restfulpy.configuration import configure


__version__ = '0.1.0-planning.1'


class Application:

    def __init__(self, name: str, root: Controller, root_path='.', config=None):
        self.config = config
        self.root = root
        self.root_path = abspath(root_path)
        self.name = name
        self.cli_main = MainLauncher(self)

    def configure(self, files=None, **kwargs):

        context = {
            'data_dir': join(self.root_path, 'data'),
            'restfulpy_dir': abspath(dirname(__file__))
        }

        files = files or []
        local_config_file = join(user_config_dir(), '%s.yml' % self.name)
        if exists(local_config_file):
            print('Loading config file: %s' % local_config_file)
            files.insert(0, local_config_file)

        configure(config=self.config, files=files, context=context, **kwargs)

    def insert_base_data(self):
        raise NotImplementedError

    def insert_mockup_data(self):
        raise NotImplementedError


__all__ = [
    'Application'
]
