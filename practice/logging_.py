import logging
from logging.handlers import RotatingFileHandler

file_handler = RotatingFileHandler(
    'root.log',
    encoding='utf-8',
    maxBytes=5242880
)


logging.basicConfig(level=logging.DEBUG, handlers=[file_handler])

my_logger = logging.getLogger('MyLogger')
my_logger.addHandler(file_handler)
my_logger.propagate = False



if __name__ == '__main__':
    logging.info('First Log')
    my_logger.info('Second log')
