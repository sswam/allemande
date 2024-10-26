""" This module is used to configure logging. """

import os
import sys
import logging
from logging import Formatter
import logging.config
import argparse
from pathlib import Path
from collections import deque
from typing import Callable
from contextlib import contextmanager
import functools
import inspect

from ally import meta

__version__ = "0.1.3"

logs = sys.modules[__name__]


console_formatter_normal = logging.Formatter("%(message)s")

console_formatter_debug = logging.Formatter("%(asctime)s  %(levelname)-8s  %(name)s  %(message)s")

file_formatter = logging.Formatter("%(asctime)s  PID:%(process)d  %(levelname)-8s  %(name)s  %(message)s")


def setup_logging():
    """Set up logging, before parsing CLI arguments."""
    script_name = meta.get_script_name()

    # Check for a logging.ini file in the script's directory
    logging_config_file = Path(script_name).parent / "logging.ini"
    if logging_config_file.exists():
        logging.config.fileConfig(logging_config_file)
        return

    get_logger(root=True)


def get_log_dir():
    """Get the directory for log files, creating it if necessary."""
    log_dir = os.path.expanduser("~/.logs")
    os.makedirs(log_dir, exist_ok=True, mode=0o700)
    return log_dir


def get_logger(level=1, root=False, name=None, indent=False, log_level="WARNING", **kwargs) -> logging.Logger:
    """Get a logger for the calling module, or named logger."""
    script_name = meta.get_script_name()

    if root:
        logger = logging.getLogger()
        name = None
    else:
        name = name or meta.get_module_name(level + 1)
        logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.propagate = False

    # Wrap the logger in an IndentLogger if requested
    if indent:
        logger = logs.IndentLogger(logger, **kwargs)

    # Set up the console handler
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)

    log_dir = get_log_dir()

    # Modules log to the script file at a configurable log level, default WARNING
    # For the root logger, this will be at DEBUG level
    if script_name != name:
        script_log_file = os.path.join(log_dir, f"{script_name}.log")
        script_file_handler = logging.FileHandler(script_log_file)
        script_file_handler.setFormatter(file_formatter)
        logger.addHandler(script_file_handler)

    # Create a module file handler, log level DEBUG
    if name:
        module_log_file = os.path.join(log_dir, f"{name}.log")
        file_handler = logging.FileHandler(module_log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Set the log level for the console handler and module file handler
    _set_log_level(log_level, name=name)

    # Log the start of the script, hopefully creating the log file
    logger.debug(f"Starting {name or script_name}")

    # Set file permissions to be owner read/write only
    for handler in logger.handlers:
        if not isinstance(handler, logging.FileHandler):
            continue
        os.chmod(handler.baseFilename, 0o600)

    return logger


def get_log_level(name=None, root=False) -> str:
    """Get the current log level for the console handler."""
    if root:
        logger = logging.getLogger()
    else:
        logger = logs.get_logger(1, name=name)
    if not logger.handlers:
        return "WARNING"  # Default log level if no handlers
    return logging.getLevelName(logger.handlers[0].level)


def set_log_level(log_level: str|int, name=None, root=False) -> None:
    """Set the log level for the console handler and module file handler."""
    logger = get_logger(2, name=name, root=root)
    _set_log_level(log_level, name=logger.name)


def _set_log_level(log_level: str|int, name=None) -> None:
    """Set the log level for the console handler and module file handler."""
    if name:
        logger = logging.getLogger(name)
    else:
        logger = logging.getLogger()

    if not logger.handlers:
        return

    if isinstance(log_level, str):
        log_level_int = getattr(logging, log_level.upper())
    else:
        log_level_int = log_level
        log_level = logging.getLevelName(log_level_int)

    logger.setLevel(0)

    console_handler = logger.handlers[0]
    console_handler.setLevel(log_level_int)
    if log_level_int == logging.DEBUG:
        console_formatter = console_formatter_debug
    else:
        console_formatter = console_formatter_normal
    console_handler.setFormatter(console_formatter)

    # If we have 3 handlers, the second one is the script file handler ... hopefully! xD
    if len(logger.handlers) >= 3:
        script_file_handler = logger.handlers[1]
        script_file_handler.setLevel(log_level_int)


class IndentLogger:
    """Logger that indents messages based on the current indent level."""
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


def dump_logging_config(put: Callable = print):
    """Dump the current logging configuration with detailed information"""
    put("=== Logging Configuration ===")

    # Root logger
    root_logger = logging.getLogger()
    put(f"Root Logger Level: {logging.getLevelName(root_logger.level)}")

    # All loggers (including root)
    loggers = [root_logger] + [logging.getLogger(name) for name in logging.root.manager.loggerDict]

    for logger in loggers:
        name = logger.name if logger.name else "root"
        put(f"\nLogger: {name}")
        put(f"  Level: {logging.getLevelName(logger.level)}")
        put(f"  Propagate: {logger.propagate}")

        if not logger.handlers:
            put("  No handlers")
        else:
            for idx, handler in enumerate(logger.handlers, 1):
                put(f"  Handler {idx}: {type(handler).__name__}")
                put(f"    Level: {logging.getLevelName(handler.level)}")
                if hasattr(handler, 'baseFilename'):
                    put(f"    File: {handler.baseFilename}")
                if isinstance(handler, logging.StreamHandler):
                    put(f"    Stream: {handler.stream.name}")
                if handler.formatter:
                    put(f"    Formatter: {handler.formatter._fmt}")
                else:
                    put("    No formatter set")

    put("\n=== Potential Issues ===")
    if root_logger.level > logging.DEBUG:
        put("- Root logger level is higher than DEBUG")
    if not any(handler.level <= logging.DEBUG for handler in root_logger.handlers):
        put("- No root handlers set to DEBUG or lower")
    if not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
        put("- No FileHandler in root logger")
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        put("- No StreamHandler in root logger")

    put("\n=== Python Logging Levels ===")
    for level, name in logging._levelToName.items():
        put(f"{name}: {level}")

    put("\n=== System Information ===")
    put(f"Python Version: {sys.version}")
    put(f"Platform: {sys.platform}")


@contextmanager
def add_context(*args, **kwargs):
    """Context manager to add context to an exception."""
    try:
        yield
    except Exception as e:
        context = format_args_kwargs(args, kwargs, long=True)
        e.args = (f"{e.args[0]}\n{context}",) + e.args[1:]
        raise


# TODO often we only want to show one argument, or part of an argument
def context(*dec_args, **dec_kwargs):
    """Function decorator to add context to an exception."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            arg_names = inspect.getfullargspec(func).args
            func_args = format_args_kwargs(args, kwargs, arg_names, long=True)
            with add_context(func.__name__, func_args, *dec_args, **dec_kwargs):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def format_args_kwargs(args, kwargs, arg_names=None, long=False):
    """Format function arguments and keyword arguments for logging."""
    if long:
        sep, end, equ = "\n", "\n", ": "
    else:
        sep, end, equ = ", ", "", "="
    if arg_names:
        formatted_args = [f"{name}{equ}{arg}" for name, arg in zip(arg_names, args)]
    else:
        formatted_args = [f"{arg}" for arg in args]
    formatted_kwargs = [f"{k}{equ}{v}" for k, v in kwargs.items()]
    text = sep.join(formatted_args + formatted_kwargs)
    if text:
        text += end
    return text
