""" This module is used to configure logging. """

import os
import sys
import logging
import logging.config
import argparse
from pathlib import Path
from collections import deque

from ally import meta

logs = sys.modules[__name__]


def get_logger(level=0, indent=False, **kwargs) -> logging.Logger:
    """
    Get a logger for the calling module.

    Returns:
        logging.Logger: Logger instance for the calling module.
    """
    logger = logging.getLogger(meta.get_module_name(level + 2))
    if indent:
        logger = logs.IndentLogger(logger, **kwargs)
    return logger


def get_log_level() -> str:
    """
    Get the current log level for the console handler.

    Returns:
        str: The current log level.
    """
    logger = logs.get_logger(1)
    if not logger.handlers:
        return "WARNING"  # Default log level if no handlers
    return logging.getLevelName(logger.handlers[0].level)


def setup_logging(module_name: str, log_level: str | None = None, test=False):
    """
    Set up logging configuration based on the specified log level.
    Also logs to a file at DEBUG level.

    Args:
        module_name (str): The name of the module for which logging is being set up.
        log_level (str): The desired logging level (DEBUG, INFO, ERROR, or None).
    """

    script_name = meta.get_script_name()
    # TODO log all messages to console, file for the script, and file for the module

    logging_config_file = Path(__file__).parent / "logging.ini"

    if log_level is None:
        return

    if isinstance(log_level, str):
        log_level_int = getattr(logging, log_level.upper())
    else:
        log_level_int = log_level
        log_level = logging.getLevelName(log_level_int)

    log_dir = os.path.expanduser("~/.logs")
    os.makedirs(log_dir, exist_ok=True, mode=0o700)
    log_file = os.path.join(log_dir, f"{module_name}.log")

    logger = logs.get_logger(2)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(log_level_int)

    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    if log_level_int == logging.DEBUG:
        console_formatter = logging.Formatter(
            "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
        )
    else:
        console_formatter = logging.Formatter("%(message)s")

    file_formatter = logging.Formatter(
        "%(asctime)s  PID:%(process)d  %(levelname)-8s  %(name)s  %(message)s"
    )

    ch.setFormatter(console_formatter)
    fh.setFormatter(file_formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)

#    logger.debug(f"Starting {module_name}")

    if test:
        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")
        logger.critical("This is a critical message")

    # Set file permissions to be owner read/write only
    os.chmod(log_file, 0o600)


class IndentLogger:
    def __init__(self, logger, indent_str="\t"):
        self.logger = logger
        self.indent_str = indent_str
        self.indent_level = 0

    def indent(self, level):
        self.indent_level += level

    def _log(self, level, msg, *args, **kwargs):
        indented_msg = self.indent_str * self.indent_level + msg
        getattr(self.logger, level)(indented_msg, *args, **kwargs)

    def __getattr__(self, name):
        if name in ["debug", "info", "warning", "error", "critical"]:
            return lambda msg, *args, **kwargs: self._log(name, msg, *args, **kwargs)
        return getattr(self.logger, name)


class DeferredLogger(logging.LoggerAdapter):
    def __init__(self, name):
        super().__init__(logging.getLogger('dummy'), {})
        self._name = name
        self.dummy_logger = logging.getLogger('dummy')
        self.real_logger = None
        self.deferred_messages = deque()
        self.is_real_logger_set = False

    @property
    def name(self):
        return self._name

    def __getattr__(self, name):
        if not self.is_real_logger_set and logging.getLogger(self.name) is not logging.root:
            self.set_real_logger(logging.getLogger(self.name))
        return getattr(self.real_logger or self.dummy_logger, name)

    def set_real_logger(self, logger):
        self.real_logger = logger
        self.is_real_logger_set = True
        self._forward_deferred_messages()

    def _forward_deferred_messages(self):
        while self.deferred_messages:
            level, msg, args, kwargs = self.deferred_messages.popleft()
            getattr(self.real_logger, level)(msg, *args, **kwargs)

    def _log(self, level, msg, *args, **kwargs):
        if self.is_real_logger_set:
            getattr(self.real_logger, level)(msg, *args, **kwargs)
        else:
            logging.getLogger(self.name).debug(f"Deferred message: {msg}")
            self.deferred_messages.append((level, msg, args, kwargs))

    def debug(self, msg, *args, **kwargs):
        self._log('debug', msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log('info', msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log('warning', msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log('error', msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log('critical', msg, *args, **kwargs)


def deferred_logger_test():
    # Usage
    logger = DeferredLogger('my_logger')

    # These messages will be stored
    logger.info("This is an early info message")
    logger.error("This is an early error message")

    # Later, when you set up your logging
    logging.basicConfig(level=logging.INFO)

    # The real logger is now set, and deferred messages are forwarded
    logger.warning("This is a new warning message")

    # You can also manually set the real logger if needed
    # custom_logger = logging.getLogger('custom')
    # logger.set_real_logger(custom_logger)

deferred_logger_test()
