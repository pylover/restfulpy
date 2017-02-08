
from os import path, makedirs
from logging import getLogger, Formatter, NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL, StreamHandler
from logging.handlers import RotatingFileHandler

from nanohttp import settings, LazyAttribute


_loggers = {}

_levels = {
    'notset': NOTSET,       # 0
    'debug': DEBUG,         # 10
    'info': INFO,           # 20
    'warning': WARNING,     # 30
    'error': ERROR,         # 40
    'critical': CRITICAL    # 50
}


def create_logger(logger_name):
    config = settings.logging

    # Rebasing with default config
    cfg = config.loggers.default.copy()
    cfg.update(config.loggers.get(logger_name, {}))
    level = _levels[cfg.level.lower()]

    # Creating logger
    logger_ = getLogger(logger_name.upper())
    logger_.setLevel(level)

    # Creating Formatter
    formatter_config = config.formatters[cfg.formatter]
    formatter = Formatter(formatter_config.format, formatter_config.date_format)

    # Creating Handlers
    for handler_name in cfg.handlers:
        handler_config = config.handlers.default.copy()
        handler_config.update(config.handlers.get(handler_name, {}))

        if handler_config.type == 'console':
            handler = StreamHandler()
        elif handler_config.type == 'file':
            directory = path.dirname(handler_config.filename)
            if not path.exists(directory):
                makedirs(directory)
            handler = RotatingFileHandler(
                handler_config.filename,
                encoding='utf-8',
                maxBytes=handler_config.get('max_bytes', 52428800)
            )

        if handler_config.level != 'notset':
            handler.setLevel(_levels[handler_config.level.lower()])
        else:
            handler.setLevel(level)
        # Attaching newly created formatter to the handler
        handler.setFormatter(formatter)
        logger_.addHandler(handler)

    # Adding the first log entry
    logger_.info('Logger %s just initialized' % logger_name)
    return logger_


class LoggerProxy(object):
    def __init__(self, *args, **kw):
        self.factory_args = args
        self.factory_kwargs = kw

    @LazyAttribute
    def logger(self):
        return create_logger(*self.factory_args, **self.factory_kwargs)

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
    logger_name = logger_name.upper()
    logger = _loggers.get(logger_name)
    if not logger:
        logger = _loggers[logger_name] = LoggerProxy(logger_name)
    return logger
