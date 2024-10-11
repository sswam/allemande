"""
Main module for command-line arguments, logging, and utilities.
"""

import argparse
import logging
import logging.config
import sys
from typing import Any, Callable


from ally import logs, opts

# compatibility with old usage
from ally.logs import get_logger
from ally.old import run, io


# main = sys.modules[__name__]

__version__ = '0.1.3'


def go(
    setup_args: Callable[[argparse.ArgumentParser], None],
    main_function: Callable[..., Any],
):
    """
    Main launcher function that sets up arguments, logging, and runs the main function.

    :param setup_args: Function to set up command-line arguments
    :param main_function: Main function to run
    """

    logs.setup_logging()

    # Parse command-line arguments, and finish setting up logging
    args, kwargs, put = opts.parse(main_function, setup_args)

    put = put or print

    # run the main function, catching any exceptions
    try:
        rv = main_function(*args, **kwargs)
        if isinstance(rv, int):
            sys.exit(rv)
        elif rv is not None:
            put(rv)
    except Exception as e:
        logger = logs.get_logger(1)
        logging.error(f"Error: {type(e).__name__} - {str(e)}")
        logging.debug("Full traceback:", exc_info=True)
        sys.exit(1)
