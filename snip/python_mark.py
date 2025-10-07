#!/usr/bin/env python3-allemande

"""
Insert or remove profiling marks at blank lines in Python code.
"""

import sys
from pathlib import Path
from typing import TextIO

from ally import main, logs  # type: ignore

logger = logs.get_logger()


def add_mark(is_top_level: bool, line: str, prev_line: str, mark_num: int, timing: bool) -> str | None:
    """Add a mark if we're at top level and have a blank line after non-blank."""
    if not is_top_level or line.strip() or not prev_line.strip():
        return None

    if timing:
        return 'print(f"# mark '+mark_num+f' {(time.time() - mark_time) * 1000:.1f}ms", file=sys.stderr)'
    return 'print("# mark '+mark_num+f", file=sys.stderr)'


def process_python(istream: TextIO, ostream: TextIO, remove: bool = False, timing: bool = False) -> None:
    """Process Python code, adding or removing profiling marks."""
    mark_num = 1
    prev_line = ""

    if timing:
        ostream.write("import time\nmark_time = time.time()\n")

    for line in istream:
        line = line.rstrip('\n')

        if remove:
            if not line.strip().startswith('print("# mark '):
                ostream.write(f"{line}\n")
            continue

        is_top_level = not (line.startswith(' ') or line.startswith(')') or line.startswith('}'))

        mark = add_mark(is_top_level, line, prev_line, mark_num, timing)
        if mark:
            ostream.write(f"{mark}\n")
            mark_num += 1

        ostream.write(f"{line}\n")
        prev_line = line

    # Add final mark if last line wasn't blank
    if prev_line.strip():
        mark = add_mark(True, "", prev_line, mark_num, timing)
        if mark:
            ostream.write(f"{mark}\n")


def setup_args(arg):
    """Set up command-line arguments."""
    arg("-r", "--remove", action="store_true", help="remove marks instead of adding them")
    arg("-t", "--time", action="store_true", help="add timing information to marks", dest="timing")


if __name__ == "__main__":
    main.go(process_python, setup_args)
