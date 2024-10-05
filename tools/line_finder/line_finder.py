#!/usr/bin/env python3

"""
This module finds lines in a file based on various criteria.
"""

import sys
import re
import logging
from typing import TextIO, Iterable

from argh import arg

from ally import main  # type: ignore

__version__ = "0.1.2"

logger = main.get_logger()


@arg("pattern", help="Pattern to search for")
@arg(
    "--mode",
    choices=["all", "first", "last", "first_to_end", "start_to_first", "last_to_end", "start_to_last", "between", "other"],
    default="all",
    help="Search mode",
)
@arg("--start", help="Match at start of line", action="store_true")
@arg("--end", help="Match at end of line", action="store_true")
@arg("--whole", help="Match entire line", action="store_true")
@arg("--exclude", help="Exclude matching lines (for 'other' mode)", action="store_true")
@arg("--exclude-match", help="Exclude the matched line in to_end, from_start, or between modes", action="store_true")
@arg("--between", help="Find lines between matches")
@arg("-i", "--ignore-case", help="Case-insensitive matching", action="store_true")
@arg("-r", "--regexp", help="Use Python regular expressions", action="store_true")
@arg("-w", "--wild", help="Use wildcard matching (* and ?)", action="store_true")
@arg("-s", "--lstrip", help="Strip leading whitespace, i.e. match indented start", action="store_true")
@arg("-S", "--no-rstrip", help="Do not strip trailing whitespace", dest="rstrip", action="store_false")
@arg("-n", "--numbers", help="Include line numbers", action="store_true")
@arg("-N", "--numbers_only", help="Return only line numbers", action="store_true")
def find_lines(
    pattern: str,
    mode: str = "all",
    start: bool = False,
    end: bool = False,
    whole: bool = False,
    exclude: bool = False,
    exclude_match: bool = False,
    between: str | None = None,
    ignore_case: bool = False,
    regexp: bool = False,
    wild: bool = False,
    lstrip: bool = False,
    rstrip: bool = True,
    numbers: bool = False,
    numbers_only: bool = False,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Find lines in a file based on various criteria.
    """
    get, put = main.io(istream, ostream)

    if regexp and wild:
        logger.error("Cannot use --regexp and --wild options together")
        sys.exit(1)

    result = find_lines(
        istream, pattern, mode, start, end, whole,
        not exclude, between, ignore_case, regexp, wild, exclude_match,
        lstrip, rstrip,
    )
    for line in result:
        put(line, end="")

    lines = get(lines=True)

    if whole:
        start = end = True

    if use_wild:
        # I don't think we need like {foo,bar} that's getting a bit fancy
        pattern = re.escape(pattern).replace(r'\*', '.*').replace(r'\?', '.')
    elif not use_regexp:
        pattern = re.escape(pattern)

    matches = []

    flags = re.IGNORECASE if ignore_case else 0

    if start or end:
        pattern = f"(?:{pattern})"
    if start:
        if lstrip:
            pattern = f"\s*{pattern}"
        pattern = "^" + pattern
    if end:
        if rstrip:
            pattern += "\s*$"
        pattern += "$"

    regex = re.compile(pattern, flags)

    matches = [i for i, line in enumerate(lines) if regex.search(line)]

    try:
        # TODO get line numbers first, then possibly the lines or just numbers or both
        if mode == "first":
            return [lines[matches[0]]]
        if mode == "last":
            return [lines[matches[-1]]]
        if mode == "first_to_end":
            delta = 1 if exclude_match else 0
            return lines[matches[0] + delta:]
        if mode == "start_to_first":
            delta = 0 if exclude_match else 1
            return lines[:matches[0] + delta]
        if mode == "last_to_end":
            delta = 1 if exclude_match else 0
            return lines[matches[-1] + delta:]
        if mode == "start_to_last":
            delta = 0 if exclude_match else 1
            return lines[:matches[-1] + delta]
        if between:
            # TODO need to refactor the API
            raise NotImplementedError
        `
        if mode == "other":
            return [line for i, line in enumerate(lines) if i not in matches]
    except IndexError:
        return []

    # WTF is 'include' ?!
    return [lines[i] for i in matches] if include else []


if __name__ == "__main__":
    main.run(find_lines)
