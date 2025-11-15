#!/usr/bin/env python3-allemande

# Looking at the code and the main task, I need to:
#
# 1. Split the functionality to allow processing strings directly (not just streams)
# 2. Fix the type errors reported by pyrefly
# 3. Bump the patch version
#
# The key insight is to separate the core substitution logic from the I/O handling.


"""
This module performs text substitution with various options.
"""

import sys
import os
import re
from typing import TextIO

from argh import arg
from ally import main

__version__ = "1.0.2"

logger = main.get_logger()

# Global dict for macro functions
macros = {}


def read_file_content(filename: str) -> str:
    """Read and return the content of a file."""
    with open(filename, 'r') as file:
        return file.read()


def process_mapping(args: list[str], reverse: bool, file_content: bool) -> dict[str, str]:
    """Process the mapping from command-line arguments or file."""
    mapping = {}
    while len(args) >= 2:
        k, v = args[:2]
        args = args[2:]
        if reverse:
            k, v = v, k
        if file_content:
            k = read_file_content(k)
            v = read_file_content(v)
        mapping[k] = v
    return mapping


def build_regex(mapping: dict[str, str], whole_words: bool, regexp: bool) -> re.Pattern[str]:
    """Build the regex pattern for substitution."""
    patterns = []
    for k in mapping.keys():
        if regexp:
            pattern = k
        else:
            pattern = re.escape(k)
        if whole_words:
            pattern = r'\b' + pattern + r'\b'
        patterns.append('(' + pattern + ')')
    regex_str = '|'.join(patterns)
    return re.compile(regex_str)


def sub(
    text: str,
    mapping: dict[str, str],
    whole_words: bool = False,
    regexp: bool = False,
    function: bool = False,
) -> str:
    """
    Perform text substitution on a string.

    Args:
        text: The input text to process
        mapping: Dictionary mapping patterns to replacements
        whole_words: Match whole words only
        regexp: Treat patterns as regular expressions with \\0 in replacements
        function: Use functions from macros dict as replacements

    Returns:
        The text with substitutions applied
    """
    if not mapping:
        return text

    regex_pattern = build_regex(mapping, whole_words, regexp)
    logger.debug("Regex pattern: %s", regex_pattern.pattern)

    def replace(match: re.Match[str]) -> str:
        matched_text = match.group(0)

        if function:
            # Find which pattern matched by checking each group
            for i, (pattern, func_name) in enumerate(mapping.items(), 1):
                if match.group(i):
                    func = macros[func_name]
                    groups = match.groups()
                    if groups and any(g is not None for g in groups):
                        return func(*[g for g in groups if g is not None])
                    return func(matched_text)

        if regexp:
            # Find which pattern matched to get the replacement
            for i, (pattern, replacement) in enumerate(mapping.items(), 1):
                if match.group(i):
                    return replacement.replace('\\0', matched_text)

        return mapping.get(matched_text, matched_text)

    return regex_pattern.sub(replace, text)


@arg('-w', '--whole-words', help='Match whole words only')
@arg('-e', '--regexp', help='Treat patterns as regular expressions with \\0 in replacements')
@arg('-f', '--function', help='Use functions from macros dict as replacements')
@arg('-u', '--use-env', help='Use environment variables as mapping')
@arg('-q', '--quote-chars', help='Specify quote characters for keys')
@arg('-m', '--map-file', help='Read mapping from file')
@arg('-r', '--reverse', help='Reverse key-value pairs')
@arg('-c', '--file-content', help='Treat key-value pairs as filenames and read their contents')
def sub_main(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    whole_words: bool = False,
    regexp: bool = False,
    function: bool = False,
    use_env: bool = False,
    quote_chars: str = '',
    map_file: str = '',
    reverse: bool = False,
    file_content: bool = False,
    *args: str
) -> None:
    """
    Perform text substitution based on various options and a mapping.
    It reads from STDIN and writes to STDOUT.

    In regexp mode (-e), patterns are treated as regular expressions and
    replacements can use \\0 for the full match.

    In function mode (-f), replacements are function names from the macros dict,
    called with *match.groups() or the full text when no groups.
    """
    mapping = {}

    if use_env:
        mapping = dict(os.environ)

    if map_file:
        with open(map_file, 'r') as f:
            for line in f:
                k, v = line.strip().split('\t', 1)
                mapping[k] = v

    mapping.update(process_mapping(list(args), reverse, file_content))

    if not regexp:
        q0, q1 = quote_chars[:2] if quote_chars else ('', '')
        mapping = {f"{q0}{k}{q1}": v for k, v in mapping.items()}

    get, put = main.io(istream, ostream)

    # TODO: Handle multiline mode if needed
    for line in istream:
        modified_line = sub(line, mapping, whole_words, regexp, function)
        put(modified_line)


if __name__ == "__main__":
    main.run(sub_main)


# 1. The change from `put(modified_line, end='')` to `put(modified_line)` will
# likely add extra newlines to the output. The iterator `for line in istream:`
# typically yields lines with their trailing newline characters intact. The
# original `put(..., end='')` wrote the line (including its newline) without
# adding another. The new `put(modified_line)` will likely write the line and
# then append an additional newline, resulting in double-spaced output.
