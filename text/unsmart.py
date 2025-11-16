#!/usr/bin/env python3-allemande

"""
Convert between smart typography and plain ASCII equivalents, while preserving code segments.
"""

import re
import sys
from typing import Iterator, TextIO

from ally import main  # type: ignore

__version__ = "0.1.7"


def _split_code_segments(text: str) -> Iterator[tuple[bool, str]]:
    """Yield (is_code, segment) tuples for fenced code and inline backticks."""
    pattern = r'(```[\s\S]*?```|`[^`\n]+`)'
    parts = re.split(pattern, text)
    for i, part in enumerate(parts):
        yield (i % 2 == 1, part)


def _is_likely_code(text: str) -> bool:
    """Heuristic: does this look like code?"""
    code_indicators = [
        r'\w+\s*=\s*\w',                 # assignment (single =)
        r'==|!=|<=|>=',                  # comparison operators
        r'[;{}()\[\]]',                  # syntax chars (lowered threshold)
        r'\b(if|for|def|class|function|const|let|var|import|return)\b',
    ]
    return any(re.search(pat, text) for pat in code_indicators)


def _unsmart_segment(
    segment: str,
    emdash: bool,
    quotes: bool,
    apostrophes: bool,
) -> str:
    """Convert smart typography to plain ASCII in one prose segment."""
    if emdash:
        segment = re.sub(r'[\u2014\u2013\u2015]', '-', segment)
    if quotes:
        segment = re.sub(r'[\u201c\u201d]', '"', segment)
    if apostrophes:
        segment = re.sub(r'[\u2018\u2019]', "'", segment)
    return segment


def _smart_segment(
    segment: str,
    emdash: bool,
    quotes: bool,
    apostrophes: bool,
) -> str:
    """Convert plain ASCII typography to smart equivalents in one prose segment."""
    if emdash:
        segment = re.sub(' --+ ', ' \u2014 ', segment)
        segment = re.sub('([a-zA-Z.,!?;:]) - ([a-zA-Z])', '\\1 \u2014 \\2', segment)

    if quotes:
        segment = re.sub('([\\s(\\[{]|^)"', '\\1\u201c', segment)
        segment = re.sub('"([\\s.,!?;:)\\]}]|$)', '\u201d\\1', segment)

    if apostrophes:
        segment = re.sub("([a-zA-Z])'", '\\1\u2019', segment)
        segment = re.sub("([\\s]|^)'(\\d)", '\\1\u2019\\2', segment)

        segment = re.sub("([\\s(\\[{]|^)'", '\\1\u2018', segment)
        segment = re.sub("'([\\s.,!?;:)\\]}]|$)", '\u2019\\1', segment)

    return segment


def unsmart(
    text: str,
    emdash: bool = True,
    quotes: bool = True,
    apostrophes: bool = True,
) -> str:
    """
    Convert "smart" typography to plain ASCII equivalents.

    Args:
        emdash: Convert em/en dashes to hyphens
        quotes: Convert smart double quotes to straight quotes
        apostrophes: Convert smart single quotes/apostrophes to straight quotes
    """
    result: list[str] = []
    for is_code, segment in _split_code_segments(text):
        if is_code:
            result.append(segment)
            continue
        result.append(_unsmart_segment(segment, emdash, quotes, apostrophes))
    return ''.join(result)


def smart(
    text: str,
    emdash: bool = True,
    quotes: bool = True,
    apostrophes: bool = True,
) -> str:
    """
    Convert plain ASCII typography to "smart" equivalents.

    Args:
        emdash: Convert hyphens with spaces to em dashes
        quotes: Convert straight double quotes to smart quotes
        apostrophes: Convert straight single quotes to smart apostrophes

    Heuristics:
    - Em dash: ` -- ` or ` - ` between words/punctuation
    - Opening quote: after space, start, or punctuation
    - Closing quote: before space, end, or punctuation
    - Apostrophe: after letter (it's, don't, '90s)
    """
    result: list[str] = []
    for is_code, segment in _split_code_segments(text):
        if is_code or _is_likely_code(segment):
            result.append(segment)
            continue
        result.append(_smart_segment(segment, emdash, quotes, apostrophes))
    return ''.join(result)


def unsmart_cli(
    istream: TextIO,
    ostream: TextIO,
    smart_mode: bool = False,
    emdash: bool = True,
    quotes: bool = True,
    apostrophes: bool = True,
) -> None:
    """Convert between smart and plain typography, reading from stdin and writing to stdout."""
    text = istream.read()

    if smart_mode:
        result = smart(text, emdash=emdash, quotes=quotes, apostrophes=apostrophes)
    else:
        result = unsmart(text, emdash=emdash, quotes=quotes, apostrophes=apostrophes)

    ostream.write(result)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-s", "--smart", dest="smart_mode", action="store_true", help="convert to smart typography (default is unsmart)")
    arg("--no-emdash", dest="emdash", action="store_false", help="don't convert dashes")
    arg("--no-quotes", dest="quotes", action="store_false", help="don't convert quotes")
    arg("--no-apostrophes", dest="apostrophes", action="store_false", help="don't convert apostrophes")


if __name__ == "__main__":
    # Check if invoked as 'smart' or 'smart.py'
    script_name = sys.argv[0].split('/')[-1]
    if script_name in ('smart', 'smart.py'):
        sys.argv.append('--smart')

    main.go(unsmart_cli, setup_args)


# The Unicode characters used are:
# - `\u2014` — em dash
# - `\u201c` — left double quotation mark (")
# - `\u201d` — right double quotation mark (")
# - `\u2018` — left single quotation mark (')
# - `\u2019` — right single quotation mark / apostrophe (')

# Known Issues:

# 1. The regex for parsing inline code, `` `[^`\n]+` ``, does not handle
# Markdown's use of multiple backticks to delimit code containing backticks
# (e.g., ` `` ` ``). This can lead to a fragment of the code block being
# incorrectly processed as prose. For example, input like `This is `` ` ``.`
# may be split incorrectly, with the final `` `.` treated as prose.
# 2. In `_smart_segment`, the regex for turning ` - ` into an em dash might
# be too aggressive for technical text, potentially converting command-line
# fragments like `diff -u file1 file2` if written with extra spaces.
# 3. The assertion in `test_nested_quotes` is very general. A more specific
# assertion checking for the exact expected string output would make the test
# more robust and verify the logic for nested quotes more thoroughly.
