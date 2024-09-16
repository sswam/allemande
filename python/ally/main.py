"""
Main module for setting up logging and command-line argument parsing.
"""

import logging
import argh


def setup_logging(log_level):
    """
    Set up logging configuration based on the specified log level.

    Args:
        log_level (str): The desired logging level (DEBUG, INFO, ERROR, or None).
    """
    if log_level is None:
        return

    if log_level == logging.DEBUG:
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    else:
        fmt = "%(message)s"
    logging.basicConfig(level=log_level, format=fmt)


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
    """
    Run the specified command with logging arguments.

    Args:
        command (callable): The command to be executed.
    """
    parser = setup_logging_args()
    argh.set_default_command(parser, command)
    argh.dispatch(parser)
