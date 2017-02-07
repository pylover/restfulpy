
import logging
import logging.config


logger_prefix = ''


def configure(configurations):
    # noinspection PyUnresolvedReferences
    logging.config.dictConfig(configurations)


def set_logger_prefix(prefix):
    global logger_prefix
    logger_prefix = prefix


def get_logger(name):
    return logging.getLogger('%s.%s' % (logger_prefix, name))
