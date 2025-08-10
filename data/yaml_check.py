#!/usr/bin/env python3-allemande

"""
Check YAML files for syntax errors.
"""

import yaml
import re
from ally import main  # type: ignore


def check_yaml(filename: str) -> int:
    """Check a single YAML file for syntax errors."""
    status = 0
    try:
        with open(filename, encoding='utf-8') as f:
            yaml.safe_load(f)
    except Exception as e:  # pylint: disable=broad-except
        error_msg = re.sub(r'\s+', ' ', str(e))
        print(f"{filename}\t{error_msg}")
        status = 1
    return status


def check_files(filenames: list[str]) -> int:
    """Check YAML files for syntax errors."""
    status = 0
    for filename in filenames:
        if check_yaml(filename):
            status = 1
    return status


def setup_args(arg):
    """Set up command-line arguments."""
    arg('filenames', nargs='*', help='YAML files to check')


if __name__ == "__main__":
    main.go(check_files, setup_args)

# Here's `yaml_check.py`:
