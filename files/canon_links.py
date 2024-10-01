#!/usr/bin/env python3

"""
Create symlinks in the canon directory for executable files and .sh files.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, TextIO

from ally import main

__version__ = "0.1.0"

logger = main.get_logger()


def _create_symlink(file: Path, target_dir: Path) -> None:
    filename = file.name
    stem = file.stem
    symlink_name = stem.replace('_', '-')

    relative_path = Path(os.path.relpath(file, target_dir))
    symlink_path = target_dir / symlink_name

    logger.info(f"{symlink_path}\t{relative_path}")

    different_symlink = False
    if symlink_path.is_symlink() and symlink_path.readlink() != relative_path:
        different_symlink = True
        logger.warning(f"replacing symlink: {symlink_path.readlink()} -> {relative_path}")

    if not symlink_path.is_symlink() or different_symlink:
        symlink_path.unlink(missing_ok=True)
        symlink_path.symlink_to(relative_path)


def _process_path(source: Path, target_dir: Path) -> None:
    if source.is_file():
        files = [source]
    else:
        files = source.iterdir()

    for file in files:
        if file.name.startswith('.') or file.name.count('.') > 1 or file.name.endswith('~'):
            continue
        is_executable = os.access(file, os.X_OK)
        if file.is_file() and (is_executable or file.suffix == '.sh'):
            _create_symlink(file, target_dir)


def canon_links(*sources: List[str], target_dir: str = "canon") -> None:

    """
    Create symlinks in the canon directory for executable files and .sh files.
    """
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    for source in sources:
        Path(source).mkdir(parents=True, exist_ok=True)
        _process_path(Path(source), target_path)


if __name__ == "__main__":
    main.run(canon_links)
