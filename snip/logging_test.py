#!/usr/bin/env python

import argh
import logging
from logging import StreamHandler
from logging.handlers import RotatingFileHandler


def setup_logging(log_level, log_file=None):
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatters
    debug_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    simple_formatter = logging.Formatter('%(message)s')

    # Console handler
    console_handler = StreamHandler()
    console_handler.setFormatter(debug_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if log_file is provided)
    if log_file:
        file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
        file_handler.setFormatter(debug_formatter)
        root_logger.addHandler(file_handler)

    # Set formatters based on log level
    for handler in root_logger.handlers:
        if log_level > logging.DEBUG:
            handler.setFormatter(simple_formatter)
        else:
            handler.setFormatter(debug_formatter)


@argh.arg('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO')
@argh.arg('--log-file', help='Log file path')
def main(log_level='INFO', log_file=None):
    # Set up logging
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    setup_logging(numeric_level, log_file)

    # Your main program logic here
    logging.debug("This is a debug message")
    logging.info("This is an info message")
    logging.warning("This is a warning message")
    logging.error("This is an error message")
    logging.critical("This is a critical message")


if __name__ == '__main__':
    argh.dispatch_command(main)
