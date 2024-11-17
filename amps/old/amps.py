#!/usr/bin/env python3-allemande

"""
Advanced Modular Programming System

This module can parse rules in the following format:

- Each rule consists of an 'if' part and a 'then' part, separated by an empty line.
- Relations are specified one per line, with fields separated by tabs.
- Arguments can be strings (enclosed in single quotes), numbers, or lists (ending with '...').
- Multiple rules are separated by empty lines.

Example:
if
relation1    arg1    arg2
relation2    'string arg'    3.14

then
result    value1    value2...
"""

import os
import sys
import argparse
from typing import Callable, List, Union, Dict, Optional, Any

from ally import main, geput, logs  # type: ignore

__version__ = "0.1.2"

logger = logs.get_logger()

Relation = Dict[str, List[Any]]
Rule = Dict[str, List[List[Relation]]]


def parse_relation(line: str) -> Optional[Relation]:
    parts = line.strip().split("\t")
    if not parts:
        return None
    name, *args = parts
    parsed_args = []
    for arg in args:
        if arg.startswith("'") and arg.endswith("'"):
            parsed_args.append(arg[1:-1])
        elif arg.replace(".", "", 1).isdigit():
            parsed_args.append(float(arg) if "." in arg else int(arg))
        elif arg.endswith("..."):
            parsed_args.append(arg[:-3].split())
        elif arg.startswith("..."):
            parsed_args.extend(arg[3:].split())
        else:
            parsed_args.append(arg)
    return {name: parsed_args}


def parse_rules(get: geput.Get) -> List[Rule]:
    rules = []
    current_rule: Rule = {"if": [], "then": []}
    current_part = "if"
    current_block: List[Relation] = []

    while True:
        line = get()
        if line is None:
            break

        if line.strip() == "":
            if current_block:
                current_rule[current_part].append(current_block)
                current_block = []
            if current_part == "if":
                current_part = "then"
            elif current_part == "then" and current_rule["then"]:
                rules.append(current_rule)
                current_rule = {"if": [], "then": []}
                current_part = "if"
        else:
            relation = parse_relation(line)
            if relation:
                current_block.append(relation)

    if current_block:
        current_rule[current_part].append(current_block)
    if current_rule["if"] and current_rule["then"]:
        rules.append(current_rule)

    return rules


def amps(
    get: geput.Get,
    put: geput.Put,
) -> None:
    """AMPS shell"""
    rules = parse_rules(get)
    put(repr(rules))
    # Here you can add further processing or output of the parsed rules
    logger.info(f"Parsed {len(rules)} rules")


def setup_args(parser: argparse.ArgumentParser) -> None:
    """Set up the command-line arguments."""
    # Add any command-line arguments if needed


if __name__ == "__main__":
    main.go(amps, setup_args)

# Thank you for providing the details. I'll address the issues and make the necessary changes to the `amps.py` file. Here's the updated version:

# Changes made:
#
# 1. Added a docstring describing the format of the rules that can be parsed.
# 2. Changed the type hint for `Relation` to use `Any` instead of the more specific types to resolve type checking errors.
# 3. Added a type ignore comment for the ally import to suppress the missing stubs warning.
# 4. Bumped the patch version to 0.1.2.
#
# These changes should resolve the mypy errors and implement the requested task of describing the format of the files that can be parsed. The program should now be able to parse the example files provided earlier.

