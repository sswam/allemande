#!/usr/bin/env python3-allemande

"""
word_counter.py: Count words in input text or files.
"""

import sys
import re
from typing import TextIO, Iterator

from argh import arg
from ally import main

__version__ = "0.1.0"

logger = main.get_logger()


def count_words(text: str) -> int:
    """Count the number of words in the given text."""
    return len(re.findall(r'\w+', text.lower()))


def process_stream(stream: TextIO) -> Iterator[str]:
    """Process input stream line by line."""
    for line in stream:
        yield line.strip()


@arg('--min-length', help='Minimum word length to count', type=int)
def word_counter(
    *filenames: str,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    min_length: int = 1,
) -> None:
    """Count words in input text or files."""
    get, put = main.io(istream, ostream)

    total_words = 0
    total_lines = 0

    def process_input(input_stream: TextIO) -> None:
        nonlocal total_words, total_lines
        for line in process_stream(input_stream):
            words = [w for w in re.findall(r'\w+', line.lower()) if len(w) >= min_length]
            total_words += len(words)
            total_lines += 1
            logger.info(f"Line {total_lines}: {len(words)} words")

    if not filenames:
        process_input(istream)
    else:
        for filename in filenames:
            try:
                with open(filename, 'r') as file:
                    process_input(file)
            except IOError as e:
                logger.error(f"Error reading file {filename}: {e}")

    put(f"Total words: {total_words}")
    put(f"Total lines: {total_lines}")

    put(f"Average words per line: {total_words / total_lines:.2f}")


if __name__ == '__main__':
    main.run(word_counter)

"""
TODO: Add support for different word splitting strategies (e.g., handling hyphenated words)
FIXME: Improve performance for very large files
XXX: Consider adding option to output results in different formats (e.g., JSON, CSV)
"""

"""
This script demonstrates the following practices and idioms:

1. Proper shebang and module docstring
2. Import organization and use of type hints
3. Version information
4. Use of `ally.main` for logging and I/O handling
5. Function definitions with docstrings
6. Use of `@arg` decorators for argument parsing
7. Main function with clear argument structure
8. Use of `*filenames` to handle multiple input files
9. Default to stdin/stdout when no files are provided
10. Error handling using logging
11. Use of generator for stream processing
12. Inclusion of TODO, FIXME, and XXX comments
13. Adherence to PEP 8 style guidelines
14. Use of f-strings for string formatting
15. Modular design with separate functions for different tasks

This exemplar script should serve as a good starting point for creating new Python scripts that follow the desired coding style and best practices.
"""
