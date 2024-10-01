"""
A Python module that provides lazy loading functionality for modules and
symbols.

This module implements a lazy loading mechanism for Python modules and symbols.
It allows for efficient importing of modules only when they are actually used.

The `lazy` function can be used in the following ways, for example:

import openai

    lazy('openai')

from transformers import AutoTokenizer

    lazy('transformers', 'AutoTokenizer')

import google.generativeai as genai

    lazy('google.generativeai', _as='genai')

from datetime import datetime as dt

    lazy('datetime', dt='datetime')

import openai
openai_async_client = openai.AsyncOpenAI()

    lazy('openai', openai_async_client=lambda openai: openai.AsyncOpenAI())

You can also combine several imports using the same module:

import openai
from openai import AsyncOpenAI
openai_async_client = openai.AsyncOpenAI()
perplexity_async_client = openai.AsyncOpenAI(
    base_url="https://api.perplexity.ai",
    api_key=os.environ.get("PERPLEXITY_API_KEY"),
)

    lazy(
        "openai",
        "AsyncOpenAI",
        openai_async_client=lambda openai: openai.AsyncOpenAI(),
        perplexity_async_client=lambda openai: openai.AsyncOpenAI(
            base_url="https://api.perplexity.ai",
            api_key=os.environ.get("PERPLEXITY_API_KEY"),
        ),
    )

Calling `lazy()` without arguments will trigger the loading of all requested
modules and symbols in a background coroutine, yielding between each load.

Calling `lazy(0.1)` with a number will async sleep for the given time, then
trigger loading as above.

The `lazy` function returns a list of `LazyProxy` objects in order, but you
should not normally need to use them directly, as it messes with the calling
global namespace. If you don't want to mess with the namespace, you can use the
`lazy_load` function instead. But that's not very lazy of you!
"""

import sys
import logging
import importlib
from types import ModuleType
from typing import Callable, Any
import asyncio

__version__ = "0.1.12"  # Bumped patch version

logger = logging.getLogger(__name__)


module_proxies = {}
maybe_unloaded_proxies = []


class LazyProxy:
    def __init__(self, loader):
        self._LazyProxy_loader = loader
        self._LazyProxy_target = None
        maybe_unloaded_proxies.append(self)

    def _LazyProxy_load(self):
        value = self._LazyProxy_target
        if value is None:
            value = self._LazyProxy_target = self._LazyProxy_loader()
        return value

    def __getattribute__(self, name):
        if name.startswith("_LazyProxy_"):
            return object.__getattribute__(self, name)
        return getattr(self._LazyProxy_load(), name)

    def __setattr__(self, name, value):
        if name.startswith("_LazyProxy_"):
            return object.__setattr__(self, name, value)
        setattr(self._LazyProxy_load(), name, value)

    def __delattr__(self, name):
        delattr(self._LazyProxy_load(), name)

    def __dir__(self):
        return dir(self._LazyProxy_load())

    def __repr__(self):
        return repr(self._LazyProxy_load())

    def __call__(self, *args, **kwargs):
        return self._LazyProxy_load()(*args, **kwargs)

    # TODO add more magic methods if and when needed


def load_all_modules():
    global maybe_unloaded_proxies
    for proxy in maybe_unloaded_proxies:
        proxy._LazyProxy_load()
    maybe_unloaded_proxies = []


def lazy(
    arg0: str | int | float = None,
    *symbol_names,
    _as=None,
    mess_with_namespace=True,
    **kwargs: dict[str, str | Callable[[ModuleType], Any]],
) -> list[LazyProxy]:
    """Create a lazy loading proxies for modules and symbols."""
    if arg0 is None or isinstance(arg0, (int, float)):
        delay = arg0 or 0
        loop = asyncio.get_event_loop()
        loop.call_later(
            delay, lambda: asyncio.run_coroutine_threadsafe(load_all_modules(), loop)
        )
        return []

    module_name = arg0

    caller_namespace = sys._getframe(1).f_globals if mess_with_namespace else {}

    def load_module():
        logger.debug(f"Lazy loading module: {module_name}")
        module = importlib.import_module(module_name)
        caller_namespace[_as or module_name] = module
        return module

    def load_symbol(symbol_name: str, _as=None):
        logger.debug(f"Lazy loading symbol '{symbol_name}' from module '{module_name}'")
        module = load_module()
        try:
            value = getattr(module, symbol_name)
            caller_namespace[_as or symbol_name] = value
            return value
        except AttributeError as e:
            logger.error(f"Symbol '{symbol_name}' not found in module '{module_name}'")
            raise e

    def load_and_initialize(symbol_name: str, fn: Callable[[ModuleType], Any]):
        module = load_module()
        try:
            value = fn(module)
            caller_namespace[symbol_name] = value
            return value
        except Exception as e:
            logger.error(f"Error initializing variable: {e}")
            raise e

    proxy = module_proxies.get(module_name)
    if not proxy:
        proxy = LazyProxy(load_module)
        module_proxies[module_name] = proxy
    caller_namespace[_as or module_name] = proxy
    rv = [proxy]

    for symbol_name in symbol_names:
        proxy = LazyProxy(lambda: load_symbol(symbol_name))
        caller_namespace[symbol_name] = proxy
        rv.append(proxy)

    for symbol_name, target in kwargs.items():
        if isinstance(target, str):
            proxy = LazyProxy(lambda: load_symbol(target, _as=symbol_name))
        elif callable(target):
            proxy = LazyProxy(lambda: load_and_initialize(symbol_name, target))
        else:
            raise ValueError(f"Invalid target for symbol '{symbol_name}'")
        caller_namespace[symbol_name] = proxy
        rv.append(proxy)

    return rv


def lazy_load(*args, **kwargs):
    """Alias for `lazy()` function with mess_with_namespace=False."""
    return lazy(*args, mess_with_namespace=False, **kwargs)
