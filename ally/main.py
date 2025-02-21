"""
Main module for command-line arguments, logging, and utilities.
"""

import argparse
import logging
import logging.config
import sys
from typing import Any, Callable
import asyncio
import inspect
from types import SimpleNamespace
from pathlib import Path

from ally import logs, opts

# compatibility with old usage
from ally.logs import get_logger, meta
from ally.old import run, io


# main = sys.modules[__name__]

__version__ = '0.1.3'


def go(
    main_function: Callable[..., Any],
    setup_args: Callable[[argparse.ArgumentParser], None] | None = None,
    ally_output: bool = True,
    **kwargs: Any,
):
    """
    Main launcher function that sets up arguments, logging, and runs the main function.

    :param main_function: Main function to run
    :param setup_args: Function to set up command-line arguments
    """

    logs.setup_logging()

    # Parse command-line arguments, and finish setting up logging
    args, kwargs1, put = opts.parse(main_function, setup_args)
    kwargs.update(kwargs1)
    sig = inspect.signature(main_function)

    if not put:
        put = lambda s: print(s, end="")

    # run the main function, catching any exceptions
    try:
        main_function_real = main_function
        if "opts" in sig.parameters:
            main_function = lambda *args, **kwargs: meta.call_gently(main_function_real, *args, **kwargs)
        if inspect.iscoroutinefunction(main_function_real):
            rv = asyncio.run(main_function(*args, **kwargs))
        else:
            rv = main_function(*args, **kwargs)
        if isinstance(rv, int):
            sys.exit(rv)
        elif ally_output and rv is not None:
            put(str(rv).rstrip("\n") + "\n")
    except Exception as e:
        logger = logs.get_logger(2)
        logging.error(f"Error: {type(e).__name__} - {str(e)}")
        logging.debug("Full traceback:", exc_info=True)
        sys.exit(1)


def prog_info():
    """Get info about the program"""
    # TODO maybe module name, check logs code has something similar
    prog = SimpleNamespace()
    prog.path = Path(sys.argv[0]).resolve()
    prog.dir = prog.path.parent
    prog.filename = prog.path.name
    prog.name = prog.path.stem
    return prog
