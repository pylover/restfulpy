
from os import path, makedirs
from logging import getLogger, FileHandler, Formatter, NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL, StreamHandler

from nanohttp import settings


_loggers = {}

_levels = {
    'notset': NOTSET,
    'debug': DEBUG,
    'info': INFO,
    'warning': WARNING,
    'error': ERROR,
    'critical': CRITICAL
}


def create_logger(logger_name):
    config = settings.logging
    logger_config = config.loggers.get(logger_name, config.loggers.default)

    # Rebasing with default config
    cfg = config.loggers.default.copy()
    cfg.update(logger_config)
    level = _levels[cfg.level]

    # Creating logger
    logger_ = getLogger(logger_name.upper())
    logger_.setLevel(level)

    # Creating Formatter
    formatter_config = config.formatters[cfg.formatter]
    formatter = Formatter(formatter_config.format, formatter_config.date_format)

    # Creating Handlers
    for handler_name in cfg.handlers:
        handler_config = config.handlers[handler_name]
        if handler_config.type == 'console':
            handler = StreamHandler()
        elif handler_config.type == 'file':
            directory = path.dirname(handler_config.filename)
            if not path.exists(directory):
                makedirs(directory)
            handler = FileHandler(handler_config.filename, encoding='utf-8')
        handler.setLevel(level)
        # Attaching newly created formatter to the handler
        handler.setFormatter(formatter)
        logger_.addHandler(handler)

    # Adding the first log entry
    logger_.info('Logger %s just initialized' % logger_name)
    return logger_


class LoggerProxy(object):
    def __init__(self, *args, **kw):
        self._internal_logger = None
        self.factory_args = args
        self.factory_kwargs = kw

    @property
    def logger(self):
        if not self._internal_logger:
            self._internal_logger = create_logger(*self.factory_args, **self.factory_kwargs)
        return self._internal_logger

    def info(self, *args, **kw):
        self.logger.info(*args, **kw)

    def debug(self, *args, **kw):
        self.logger.debug(*args, **kw)

    def error(self, *args, **kw):
        self.logger.error(*args, **kw)

    def warning(self, *args, **kw):
        self.logger.warning(*args, **kw)

    def critical(self, *args, **kw):
        self.logger.critical(*args, **kw)

    def exception(self, *args, **kw):
        self.logger.exception(*args, **kw)


def get_logger(logger_name='main'):
    logger = _loggers.get(logger_name)
    if not logger:
        logger = _loggers[logger_name] = LoggerProxy(logger_name)
    return logger
