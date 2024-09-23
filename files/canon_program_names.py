#!/usr/bin/env python3

"""
Find program files with dashes in their names, and suggest better names with underscores.
Use together with canon, which creates symlinks having names with dashes.
This nonsense is so that we can have Python modules with underscores, and executables with dashes
and no extension, including executables that are Python modules.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, TextIO
import re

from ally import main

__version__ = "0.1.0"

logger = main.get_logger()


def _check_file(file: Path) -> None:
    filename = file.name
    ext = file.suffix

    try:
        shebang = open(file).readline().strip()
    except UnicodeDecodeError:
        logger.warning(f"not a text file? {file}")
        return

    if not ext and shebang.startswith("#!"):
        if re.search(r"\b(python|python3)\b", shebang):
            ext = ".py"
        elif re.search(r"\b(bash|sh)\b", shebang):
            ext = ".sh"
        elif re.search(r"\bperl\b", shebang):
            ext = ".pl"
        elif re.search(r"\bcz\b", shebang):
            ext = ".cz"
        else:
            logger.warning(f"unknown shebang: {shebang}")

    if not ext and not shebang:
        logger.warning(f"assuming shell script: {file}")
        ext = ".sh"

    good_name = file.stem.replace('-', '_') + ext

    if good_name != filename:
        print(f"{filename}\t{good_name}")


def _process_path(source: Path) -> None:
    if source.is_file():
        files = [source]
    else:
        files = source.iterdir()

    for file in files:
        if file.name.startswith('.') or file.name.count('.') > 1:
            continue
        is_executable = os.access(file, os.X_OK)
        if file.is_file() and (is_executable or file.suffix == '.sh'):
            _check_file(file)


def canon_program_names(*sources: List[str]) -> None:
    for source in sources:
        _process_path(Path(source))


if __name__ == "__main__":
    main.run(canon_program_names)
