#!/usr/bin/env python3

"""
env-detective.py - A script to search for possible sources of an environment variable.

This script investigates various configuration files and system settings
to determine where an environment variable might have been set.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
from shutil import which
import re
import glob

from argh import arg
import sh

from ally import main

__version__ = "1.0.0"


logger = main.get_logger(indent=True, indent_str=4 * " ")


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


def check_source_command(line: str, expanded_path: Path, var_name: str, checked_files: List[str], level: int) -> Optional[str]:
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

    result = check_config_file(str(sourced_path), var_name, checked_files, level)
    if result:
        logger.info(f"Found {var_name} in sourced file: {sourced_path}")
        return result

    return None


def check_config_file(file_path: str, var_name: str, checked_files: List[str], level: int) -> Optional[str]:
    expanded_path = Path(file_path).expanduser().resolve()

    if expanded_path.as_posix() in checked_files:
        return None

    logger.info(f"Checking file: {expanded_path}")

    try:
        level += 1
        logger.indent(1)

        checked_files.append(expanded_path.as_posix())

        if not expanded_path.exists():
            logger.warning(f"File does not exist: {expanded_path}")
            return None

        try:
            content = expanded_path.read_text()
            for line_number, line in enumerate(content.splitlines(), 1):
                line = line.strip()

                if var_name in line and not line.startswith("#"):
                    logger.info(f"Found {var_name} in {expanded_path} at line {line_number}")
                    return str(expanded_path), line_number, line

                result = check_source_command(line, expanded_path, var_name, checked_files, level)
                if result:
                    return result
        except Exception as e:
            logger.warning(f"Error reading {expanded_path}: {e}")
    finally:
        level -= 1
        logger.indent(-1)

    return None


def check_config_files(var_name: str) -> Dict[str, Optional[str]]:
    results = {}
    checked_files = []
    for file_path in COMMON_CONFIG_FILES:
        if "*" in file_path:
            files = glob.glob(file_path)
        else:
            files = [file_path]
        for file_path in files:
            result = check_config_file(file_path, var_name, checked_files, 0)
            results[file_path] = result
    return results


@arg("var_name", help="Name of the environment variable to investigate")
def investigate_env_var(var_name: str) -> None:
    global logger

    logger.info(f"Investigating sources of {var_name} environment variable")

    if main.get_log_level() not in ["DEBUG", "INFO"]:
        logger.indent_str = ""

    current_value = os.environ.get(var_name)

    if current_value is None:
        logger.warning(f"{var_name} not found in current environment")
    else:
        logger.info(f"Current {var_name} value: {repr(current_value)}")

    config_results = check_config_files(var_name)

    output = []

    for file_path, result in config_results.items():
        if not result:
            continue
        file, line_number, line = result
        logger.info(f"Found from {file_path} in {file} at line {line_number}: {line}")
        output.append("\t".join([file_path, file, str(line_number), line]))

    if not current_value and not any(config_results.values()):
        logger.info(f"{var_name} not found in any checked locations")

    for line in output:
        print(line)

if __name__ == "__main__":
    main.run(investigate_env_var)
