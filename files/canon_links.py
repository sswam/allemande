#!/usr/bin/env python3

"""
Create symlinks in the canon directory for executable files and .sh files.
"""

import os
import sys
import shutil
from pathlib import Path
from typing import TextIO

from argh import arg
from ally import main

__version__ = "0.1.2"

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
        target_dir.mkdir(parents=True, exist_ok=True)
        symlink_path.unlink(missing_ok=True)
        symlink_path.symlink_to(relative_path)


def _process_path(source: Path, target_dir: Path) -> None:
    if source.is_file():
        _process_file(source, target_dir)
    else:
        _process_directory(source, target_dir)


def _process_directory(source_dir: Path, target_dir: Path) -> None:
    for item in source_dir.iterdir():
        if item.name.startswith('.') or item.name.count('.') > 1 or item.name.endswith('~'):
            continue

        relative_path = item.relative_to(source_dir)
        new_relative_path = str(relative_path).replace('_', '-') + ".d"
        new_target = target_dir / new_relative_path

        if item.is_dir():
            _process_directory(item, new_target)
        else:
            _process_file(item, new_target.parent)


def _process_file(file: Path, target_dir: Path) -> None:
    is_executable = os.access(file, os.X_OK)
    if is_executable or file.suffix == '.sh':
        _create_symlink(file, target_dir)


def _remove_dead_links(target_dir: Path) -> None:
    for symlink in target_dir.iterdir():
        if symlink.is_symlink() and not symlink.resolve().exists():
            logger.info(f"Removing dead link: {symlink}")
            symlink.unlink()


@arg("--target-dir", default="canon", help="Target directory for symlinks")
@arg("--clean", action="store_true", help="Clean out the target directory before creating new symlinks")
def canon_links(
    *sources: list[str],
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    target_dir: str = "canon",
    clean: bool = False,
) -> None:
    """
    Create symlinks in the canon directory for executable files and .sh files.
    """
    target_path = Path(target_dir)

    if clean:
        logger.info(f"Cleaning out {target_path}")
        shutil.rmtree(target_path, ignore_errors=True)

    target_path.mkdir(parents=True, exist_ok=True)

    for source in sources:
        Path(source).mkdir(parents=True, exist_ok=True)
        _process_path(Path(source), target_path)

    _remove_dead_links(target_path)


if __name__ == "__main__":
    main.run(canon_links)
