"""
Main module for logging, command-line arguments, and utilities.
"""

import os
import sys
import logging
import traceback
import argh
import inspect
from typing import TextIO, Optional

from ally import terminal


def get_module_name(level: int = 1, ext: bool = False):
    caller_frame = inspect.stack()[level]
    caller_module = inspect.getmodule(caller_frame[0])
    module_name = os.path.basename(caller_module.__file__)
    if ext:
        return module_name
    return os.path.splitext(module_name)[0]


def get_script_name(ext: bool = False):
    script_name = os.path.basename(sys.argv[0])
    if ext:
        return script_name
    return os.path.splitext(script_name)[0]


def get_logger():
    return logging.getLogger(get_module_name(2))


def setup_logging(module_name: str, log_level: Optional[str] = None):
    """
    Set up logging configuration based on the specified log level.
    Also logs to a file at DEBUG level.

    Args:
        log_level (str): The desired logging level (DEBUG, INFO, ERROR, or None).
    """
    if log_level is None:
        return

    log_dir = os.path.expanduser("~/.logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{module_name}.log")

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


def setup_logging_args(module_name):
    """
    Set up command-line argument parsing for logging options.

    Returns:
        argh.ArghParser: Configured argument parser.
    """

    # Get the log_level from {SCRIPT_NAME}_LOG_LEVEL, or WARNING.
    log_level_var_name = f"{module_name.upper()}_LOG_LEVEL"
    default_log_level = os.environ.get(log_level_var_name, "WARNING")
    default_log_level = getattr(logging, default_log_level)

    parser = argh.ArghParser()
    parser.add_argument(
        "--log-level",
        default=default_log_level,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_const",
        const=logging.DEBUG,
        dest="log_level",
        help="Set logging level to DEBUG",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const=logging.ERROR,
        dest="log_level",
        help="Set logging level to ERROR",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const=logging.INFO,
        dest="log_level",
        help="Set logging level to INFO",
    )
    return parser


def run(command):
    module_name = get_module_name(2)
    parser = setup_logging_args(module_name)
    argh.set_default_command(parser, command)

    # Parse arguments without dispatching
    args = parser.parse_args()

    # Setup logging based on parsed arguments
    setup_logging(module_name, args.log_level)

    try:
        argh.dispatch(parser)
    except Exception as e:
        logger = logging.getLogger(sys._getframe(1).f_globals["__name__"])
        logger.error(f"Error: %s %s", type(e).__name__, str(e))
        tb = traceback.format_exc()
        logger.debug("Full traceback:\n%s", tb)


def io(istream: TextIO = sys.stdin, ostream: TextIO = sys.stdout):
    is_tty = terminal.is_terminal(istream) and terminal.is_terminal(ostream)

    def put(*args, **kwargs):
        print(*args, file=ostream, **kwargs)

    def get(prompt=": "):
        if is_tty:
            terminal.setup_history()
            return terminal.input(prompt)
        else:
            return istream.readline().rstrip("\n")

    return get, put
