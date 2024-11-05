#!/usr/bin/env python3

"""
env-detective.py - A script to search for possible sources of environment variables.

This script investigates various configuration files and system settings
to determine where environment variables might have been set.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from shutil import which
import re
import glob

import sh

from ally import main, logs

__version__ = "1.0.2"


logger = logs.get_logger(indent=True, indent_str=4 * " ")


COMMON_CONFIG_FILES = [
    "~/.bashrc",
    "~/.bash_profile",
    "~/.profile",
    "~/.zshrc",
    "/etc/profile",
    "/etc/profile.d/*",
    "/etc/environment",
]


def expand_complex_vars(path):
    def replace_var(match):
        var = match.group(1)
        default = match.group(2)
        return os.environ.get(var) or os.path.expandvars(default)

    pattern = r'\$\{([^:}]+):-([^}]+)\}'
    expanded = re.sub(pattern, replace_var, path)
    return os.path.expandvars(expanded)


def check_source_command(line: str, expanded_path: Path, var_names: List[str], checked_files: Set[str], level: int, all_files: Set[str]) -> Optional[Tuple[str, str, int, str]]:
    if not re.match(r'^\s*(source|\.) ', line):
        return None

    logger.debug(f"Checking source command: {line}")

    sourced_file = re.split(r'\s+', line.strip(), 1)[1].strip('"\'')

    sourced_file = expand_complex_vars(os.path.expandvars(sourced_file))
    if re.search(r'\$[\w\{]', sourced_file):
        logger.warning(f"Failed to expand vars in path, probably undefined: {sourced_file}")
        return None

    sourced_path = Path(sourced_file).expanduser()
    logger.debug(f"Expanded source path: {sourced_path}")

    logger.info(f"Found source command `{line}`, checking file: {sourced_file}")

    if not sourced_path.is_absolute():
        sourced_path = which(sourced_path.name, 0) or expanded_path.parent / sourced_path

    if not sourced_path:
        logger.warning(f"Sourced file not found: {sourced_file}")
        return None

    result = check_config_file(str(sourced_path), var_names, checked_files, level, all_files)
    if result:
        logger.info(f"Found variable in sourced file: {sourced_path}")
        return result

    return None


def check_config_file(file_path: str, var_names: List[str], checked_files: Set[str], level: int, all_files: Set[str]) -> Optional[Tuple[str, str, int, str]]:
    expanded_path = Path(file_path).expanduser().resolve()

    if expanded_path.as_posix() in checked_files:
        return None

    logger.info(f"Checking file: {expanded_path}")

    try:
        level += 1
        logger.indent(1)

        checked_files.add(expanded_path.as_posix())
        all_files.add(expanded_path.as_posix())

        if not expanded_path.exists():
            logger.warning(f"File does not exist: {expanded_path}")
            return None

        try:
            content = expanded_path.read_text()
            for line_number, line in enumerate(content.splitlines(), 1):
                line = line.strip()
                line_no_comment = re.sub(r'#.*', '', line)  # good enough

                for var_name in var_names:
                    if re.search(r'\b' + re.escape(var_name) + r'\b', line_no_comment):
                        logger.info(f"Found {var_name} in {expanded_path} at line {line_number}")
                        return str(expanded_path), var_name, line_number, line

                result = check_source_command(line, expanded_path, var_names, checked_files, level, all_files)
                if result:
                    return result
        except Exception as e:
            logger.warning(f"Error reading {expanded_path}: {e}")
    finally:
        level -= 1
        logger.indent(-1)

    return None


def check_config_files(var_names: List[str]) -> Tuple[Dict[str, Optional[Tuple[str, str, int, str]]], Set[str]]:
    results = {}
    checked_files = set()
    all_files = set()
    for file_path in COMMON_CONFIG_FILES:
        if "*" in file_path:
            files = glob.glob(file_path)
        else:
            files = [file_path]
        for file_path in files:
            result = check_config_file(file_path, var_names, checked_files, 0, all_files)
            results[file_path] = result
    return results, all_files


def investigate_env_var(var_names: List[str], all: bool = False) -> None:
    global logger

    logger.info(f"Investigating sources of environment variables: {' '.join(var_names)}")

    if logs.get_log_level() not in ["DEBUG", "INFO"]:
        logger.indent_str = ""

    for var_name in var_names:
        current_value = os.environ.get(var_name)

        if current_value is None:
            logger.warning(f"{var_name} not found in current environment")
        else:
            logger.info(f"Current {var_name} value: {repr(current_value)}")

    config_results, all_files = check_config_files(var_names)

    output = []

    if all:
        logger.info("Listing all rc / environment files (including sourced):")
        for file in sorted(all_files):
            print(file)
    else:
        for file_path, result in config_results.items():
            if not result:
                continue
            file, var_name, line_number, line = result
            logger.info(f"Found {var_name} from {file_path} in {file} at line {line_number}: {line}")
            output.append("\t".join([file_path, file, var_name, str(line_number), line]))

        if not any(config_results.values()):
            logger.info(f"No variables found in any checked locations")

        for line in output:
            print(line)


def setup_args(arg):
    """Set up command-line arguments."""
    arg("var_names", nargs="*", help="The environment variables to investigate")
    arg("-a", "--all", help="List all rc / environment files (including sourced)", action="store_true")


if __name__ == "__main__":
    main.go(investigate_env_var, setup_args)
