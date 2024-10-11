""" Meta-programming utilities. """

import sys
import inspect
import os
from typing import Callable
import asyncio
import functools

from ally import logs

meta = sys.modules[__name__]


def get_script_name(canon: bool = True):
    """
    Get the name of the current script.

    Args:
        canon (bool): Get the canonical name if True. Default is True.

    Returns:
        str: Name of the current script.
    """
    script_name = os.path.basename(sys.argv[0])
    if canon:
        script_name = os.path.splitext(script_name)[0]
        script_name = script_name.replace("_", "-")
    return script_name


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


def deprecated(func_name: str, replacement: str):
    """Warn that a function is deprecated."""
    if os.environ.get("ALLY_DISABLE_DEPRECATION_WARNINGS") == "1":
        return
    logger = logs.get_logger(1)
    caller = meta.get_module_name(3)
    logger.warning(
        "%s: %s is deprecated, use %s instead",
        caller,
        func_name,
        replacement,
    )


def async_to_sync_wrapper(async_func: Callable) -> Callable:
    """Wrap an async function to run synchronously."""
    if not asyncio.iscoroutinefunction(async_func):
        return async_func

    @functools.wraps(async_func)
    def wrapper(*args, **kwargs):
        return asyncio.run(async_func(*args, **kwargs))

    # Copy the signature from the async function
    wrapper.__signature__ = inspect.signature(async_func)

    # Copy all decorators from the async function
    for decorator in getattr(async_func, "__decorators__", []):
        wrapper = decorator(wrapper)

    return wrapper


def args_parameter(func):
    """Return the name of the *args catch-all parameter, if present."""
    for name, param in inspect.signature(func).parameters.items():
        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            return name
    return None


def kwargs_parameter(func):
    """Return the name of the **kwargs catch-all parameter, if present."""
    for name, param in inspect.signature(func).parameters.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return name
    return None
