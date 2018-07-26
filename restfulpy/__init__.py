import argparse
import sys
import warnings
from os.path import basename
import argcomplete

from .application import Application


warnings.filterwarnings('ignore', message='Unknown REQUEST_METHOD')


__version__ = '1.1.2a1'

