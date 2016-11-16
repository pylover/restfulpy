
from os.path import abspath

from nanohttp import Controller

from restfulpy.cli.main import MainLauncher

__version__ = '0.1.0-planning.0'


class Application:

    def __init__(self, name: str, root: Controller, root_path='.'):
        self.root = root
        self.root_path = abspath(root_path)
        self.name = name
        self.cli_main = MainLauncher(self)

    def insert_base_data(self):
        raise NotImplementedError


__all__ = [
    'Application'
]
