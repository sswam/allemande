"""
Main module for command-line arguments, logging, and utilities.
"""

import os
import sys
import logging
import logging.config
import warnings
import traceback
import inspect
from pathlib import Path
from typing import TextIO, Callable, Any, get_origin, get_args, Union
import argparse
from io import IOBase, TextIOWrapper, StringIO
import mimetypes
import asyncio
import functools
import shutil
import time
import stat

import argh

from ally import opts, logs

from ally.logs import get_logger

from ally.old import run, io, TextInput

# main = sys.modules[__name__]


def go(
    setup_args: Callable[[argparse.ArgumentParser], None],
    main_function: Callable[..., Any],
):
    """
    Main launcher function that sets up arguments, logging, and runs the main function.

    :param setup_args: Function to set up command-line arguments
    :param main_function: Main function to run
    """

    # Parse command-line arguments
    args, kwargs = opts.parse(main_function, setup_args)

    # run the main function, catching any exceptions
    try:
        main_function(*args, **kwargs)
    except Exception as e:
        logger = logs.get_logger(1)
        logging.error(f"Error: {type(e).__name__} - {str(e)}")
        logging.debug("Full traceback:", exc_info=True)
        sys.exit(1)
