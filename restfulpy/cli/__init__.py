
from .main import MainLauncher
from .base import Launcher, RequireSubCommand
from .utils import ProgressBar, LineReaderProgressBar


def main():
    from .restfulpy_ import RestfulpyMainLauncher
    RestfulpyMainLauncher()()
