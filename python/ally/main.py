"""
Main module for setting up logging and command-line argument parsing.
"""

import os
import sys
import datetime
import tempfile
import logging
import traceback

import argh

import logging
import sys


def setup_logging(log_level):
    """
    Set up logging configuration based on the specified log level.
    Also logs to a file at DEBUG level.

    Args:
        log_level (str): The desired logging level (DEBUG, INFO, ERROR, or None).
    """
    if log_level is None:
        return

    script_name = os.path.basename(sys.argv[0])
    log_dir = os.path.expanduser("~/.logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{script_name}.log")

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(log_level)

    file_formatter = logging.Formatter(
        "%(asctime)s PID:%(process)d %(levelname)s %(name)s %(message)s"
    )
    if log_level == logging.DEBUG:
        console_formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        )
    else:
        console_formatter = logging.Formatter("%(message)s")

    fh.setFormatter(file_formatter)
    ch.setFormatter(console_formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    logging.debug(f"Logging to file: {log_file}")

    # Set file permissions to be not owner read/write only
    os.chmod(log_file, 0o600)


def setup_logging_args():
    """
    Set up command-line argument parsing for logging options.

    Returns:
        argh.ArghParser: Configured argument parser.
    """
    parser = argh.ArghParser()
    parser.add_argument(
        "-d",
        "--debug",
        action="store_const",
        const="DEBUG",
        dest="log_level",
        help="Set logging level to DEBUG",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const="ERROR",
        dest="log_level",
        help="Set logging level to ERROR",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const="INFO",
        dest="log_level",
        help="Set logging level to INFO",
    )
    return parser


def run(command):
    global last_traceback
    parser = setup_logging_args()
    argh.set_default_command(parser, command)
    try:
        argh.dispatch(parser)
    except Exception as e:
        logger = logging.getLogger(sys._getframe(1).f_globals["__name__"])
        logger.error(f"Error: %s %s", type(e).__name__, str(e))
        tb = traceback.format_exc()
        logger.debug("Full traceback:\n%s", tb)
