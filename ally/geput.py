"""
Input/output utilities.

Important: These get and put functions are supposed to be very simple and very
easy to implement for different types of IO. Any functionality added should be
cosmetic, not providing essential functionality, so that another implementation
can just collect them in **kwargs and ignore them.

Wrappers should pass **kwargs along unless they use them directly.

The prompt, placeholder and flush features are examples of largely cosmetic
functionality which is okay to have in these functions. Adding an option to
strip lines or add line-endings would not be okay.
"""

import sys
import asyncio
from typing import TextIO, Callable, Iterable

from ally import titty

__version__ = "0.1.4"


Get = Callable[[str], str | None]
Put = Callable[[str], None]

# AsyncGet = AsyncCallable[[str], str|None]
# AsyncPut = AsyncCallable[[str], None]


def put_ostream(ostream: TextIO, flush=None) -> Put:
    """Create a put function for writing output."""

    if flush is None:
        flush = titty.is_tty(ostream)

    def put(line, flush=flush, **_kwargs) -> None:
        """
        Put output to an ouptput stream, BYO newlines.

        Supports flushing, which is a non-essential feature.
        """
        __builtins__["print"](line, file=ostream, end="", flush=flush)

    return put


def print(put: Put, sep=" ", end="\n") -> Put:
    """A print-like wrapper for a put function."""

    def print_fn(*args, sep=sep, end=end, **kwargs) -> None:
        """Print to a put function."""
        line = sep.join([str(arg) for arg in args]) + end
        put(line, **kwargs)

    return print_fn


def get_istream(istream: TextIO, prompt: str = ": ", placeholder: str = "") -> Get:
    """Create a get function for reading input."""

    is_tty = titty.is_tty(istream)

    def get(
        prompt: str = prompt,
        placeholder: str = placeholder,
        **_kwargs,
    ) -> str | None:
        """
        Get a line of input from an input stream, including the newline.

        Supports prompt and placeholder for TTY line-by-line input,
        which are non-essential features.
        """

        if is_tty:
            titty.setup_readline()
            return titty.get(prompt=prompt, placeholder=placeholder)

        line = istream.readline()
        if line == "":
            return None
        return line

    return get


def input(get: Get) -> Get:
    """Get a line of input without the newline."""

    def get_fn(**kwargs) -> str | None:
        line = get(**kwargs)
        if line is None:
            return None
        return line.rstrip("\r\n")

    return get_fn


def each(get: Get) -> str:
    """A generator that yields chunks from get."""
    while True:
        line = get()
        if line is None:
            break
        yield line


def foreach(func: Callable, items: Iterable) -> None:
    for item in items:
        func(item)


def inputs(get: Get) -> str:
    """A generator that yields lines from get."""
    return each(input(get))


def prints(put: Put, lines: Iterable[str]) -> None:
    """Print lines to a put function."""
    foreach(print(put), lines)


def whole(get: Get) -> str:
    """Get all input from get."""
    # TODO option to prompt if on terminal?
    return "".join(each(get))


def readline(istream: TextIO) -> Get:
    """Create a get function for reading lines from a file."""
    def get_fn(**kwargs) -> str | None:
        text = istream.readline(**kwargs)
        if text == "":
            return None
        return text
    return get_fn


def read(istream: TextIO) -> Get:
    """Create a get function for reading chunks from a file."""
    def get_fn(**kwargs) -> str | None:
        text = istream.read(**kwargs)
        if text == "":
            return None
        return text
    return get_fn


def get_list(l: list[str]) -> Get:
    """Create a get function for reading lines from a list."""
    def get_fn(**kwargs) -> str | None:
        if l:
            return l.pop(0).rstrip("\n") + "\n"
        return None
    return get_fn


def put_list(l: list[str]) -> Put:
    """Create a put function for writing to a list."""
    def put_fn(line: str, **kwargs) -> None:
        l.append(line.rstrip("\n"))
    return put_fn


def make_get_put(input_lines: list[str], output_lines: list[str]) -> tuple[Get, Put]:
    """Make get and put functions for testing."""
    return get_list(input_lines), put_list(output_lines)


# TODO maybe passing flush through is important to support.

# TODO async functions; arguably we should always use async.
#      Not using async is an optimization.
#      But I can't handle changing this to async while I'm making other changes.

# TODO streaming CSVReader, JSONLReader, etc.

# TODO maybe a get that reads a file, or a get that reads a URL.
