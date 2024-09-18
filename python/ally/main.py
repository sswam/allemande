"""
Main module for logging, command-line arguments, and utilities.
"""

import os
import sys
import logging
import traceback
import inspect
from pathlib import Path
from typing import TextIO, Callable

import argh

from ally import terminal


def get_module_name(level: int = 1, ext: bool = False):
    """
    Get the name of the calling module.

    Args:
        level (int): Stack level to inspect. Default is 1.
        ext (bool): Include file extension if True. Default is False.

    Returns:
        str: Name of the calling module.
    """
    caller_frame = inspect.stack()[level]
    caller_module = inspect.getmodule(caller_frame[0])
    module_name = os.path.basename(caller_module.__file__)
    if ext:
        return module_name
    return os.path.splitext(module_name)[0]


def get_script_name(ext: bool = False):
    """
    Get the name of the current script.

    Args:
        ext (bool): Include file extension if True. Default is False.

    Returns:
        str: Name of the current script.
    """
    script_name = os.path.basename(sys.argv[0])
    if ext:
        return script_name
    return os.path.splitext(script_name)[0]


def get_logger() -> logging.Logger:
    """
    Get a logger for the calling module.

    Returns:
        logging.Logger: Logger instance for the calling module.
    """
    return logging.getLogger(get_module_name(2))


def setup_logging(module_name: str, log_level: str | None = None):
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


def run(command: Callable) -> None:
    """
    Set up logging, parse arguments, and run the specified command.

    Args:
        command (Callable): The command function to be executed.

    Raises:
        Exception: Any exception that occurs during command execution.
    """
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


def io(istream: TextIO = sys.stdin, ostream: TextIO = sys.stdout) -> tuple[Callable, Callable]:
    """
    Create input and output functions for handling I/O operations.

    Args:
        istream (TextIO, optional): Input stream. Defaults to sys.stdin.
        ostream (TextIO, optional): Output stream. Defaults to sys.stdout.

    Returns:
        tuple[Callable, Callable]: A tuple of get and put functions.
    """
    is_tty = terminal.is_terminal(istream) and terminal.is_terminal(ostream)

    def put(*args, end="\n", **kwargs) -> None:
        """
        Print to the output stream.

        Args:
            *args: Positional arguments to print.
            **kwargs: Keyword arguments for print function.
        """
        if args and args[-1].endswith("\n"):
            end = ""
        print(*args, file=ostream, end=end, **kwargs)

    def get(prompt: str = ": ", all=False) -> str:
        """
        Get input from the input stream.

        Args:
            prompt (str, optional): Prompt to display. Defaults to ": ".

        Returns:
            str: The input string.
        """
        if all:
            return istream.read()
        if is_tty:
            terminal.setup_history()
            return terminal.input(prompt)
        else:
            return istream.readline().rstrip("\n")

    return get, put


def path(path: str) -> Path:
    """
    Construct a Path object relative to the ALLEMANDE_HOME environment variable.

    Args:
        path (str): The relative path.

    Returns:
        Path: The constructed Path object.
    """
    parts = path.replace('/', os.sep).split(os.sep)
    return Path(os.environ["ALLEMANDE_HOME"], *parts)
