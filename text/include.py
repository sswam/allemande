#!/usr/bin/env python3-allemande

"""
A simple #include preprocessor that respects indentation when including files.
"""

import sys
import logging
from pathlib import Path

from ally import main, logs, geput  # type: ignore

logger = logs.get_logger()


def process_include(line: str, indent: str) -> list[str]:
    """Process an #include directive, maintaining the indentation."""
    parts = line.strip().split(maxsplit=1)
    if len(parts) != 2:
        return [line]

    filename = parts[1].strip('"')
    try:
        content = Path(filename).read_text()
        return [indent + line for line in content.splitlines(keepends=True)]
    except FileNotFoundError:
        logger.error(f"Could not find include file: {filename}")
        raise
    except Exception as e:
        logger.error(f"Error processing include: {e}")
        raise


def include(get: geput.Get, put: geput.Put) -> None:
    """Process #include directives while preserving indentation."""
    while line := get():
        if line.lstrip().startswith("#include "):
            indent = line[:len(line) - len(line.lstrip())]
            for included_line in process_include(line.strip(), indent):
                put(included_line)
        else:
            put(line)


def setup_args(arg):
    """Set up the command-line arguments."""
    pass


if __name__ == "__main__":
    main.go(include, setup_args)
