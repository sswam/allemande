""" Input/output utilities. """

import argparse
import sys
from typing import TextIO, Callable

from ally import titty


def setup_get(istream: TextIO) -> Callable[[], str]:
    """Create a get function for reading input from a stream."""

    is_tty = titty.is_tty(istream)

    def get(
        prompt: str = ": ",
        all=False,
        lines=False,
        chunks=False,
        rstrip=True,
        placeholder="",
    ) -> str:
        """
        Get input from the input stream.

        Args:
            prompt (str, optional): Prompt to display. Defaults to ": ".
            all (bool, optional): Read all input. Defaults to False.
            lines (bool, optional): Read all lines to a list. Defaults to False.

        Returns:
            str: The input string.
        """
        if all:
            return istream.read()
        if lines or chunks:
            all_lines = istream.readlines()
            if lines and rstrip:
                all_lines = [line.rstrip() for line in all_lines]
            elif not chunks:
                all_lines = [line.rstrip("\n") for line in all_lines]
            return all_lines
        if is_tty:
            titty.setup_readline()
            return titty.get(prompt, placeholder=placeholder)
        else:
            line = istream.readline()
            if line == "":
                return None
            return line.rstrip("\n")

    return get


def setup_put(ostream: TextIO) -> Callable[[str], None]:
    """Create a put function for writing output to a stream."""

    def put(*args, end="\n", lines=False, chunks=False, rstrip=True, **kwargs) -> None:
        """
        Print to the output stream.

        Args:
            *args: Positional arguments to print.
            **kwargs: Keyword arguments for print function.
        """
        if lines or chunks:
            for arg in args:
                for line in arg:
                    if rstrip:
                        line = line.rstrip()
                    elif not chunks:
                        line = line.rstrip("\n")
                    print(line, file=ostream, end=end, **kwargs)
            return
        if args and args[-1].endswith("\n"):
            end = ""
        print(*args, file=ostream, end=end, **kwargs)

    return put
