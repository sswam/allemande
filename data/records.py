#!/usr/bin/env python3-allemande

"""
A module to read, write, and append records in a specific file format.

This module provides functions to handle a record file format with key-value pairs,
supporting multi-line strings and optional field order preservation.

Usage as a module:
    from records import read_records, write_records, append_records
"""

import sys
import logging
from typing import TextIO

from ally import main

__version__ = "1.0.1"

logger = main.get_logger()


def parse_record(lines: list[str], use_dot: bool = False) -> dict[str, str]:
    """Parse a single record from a list of lines."""
    record = {}
    field_order = []
    current_key = None
    current_value = []

    for line in lines:
        line = line.rstrip("\n")
        if not line:
            continue
        if ':' in line and not line.startswith(' ') and not line.startswith('\t'):
            if current_key:
                record[current_key] = '\n'.join(current_value).rstrip()
            current_key, value = line.split(':', 1)
            current_key = current_key.strip()
            current_value = [value.strip()]
            field_order.append(current_key)
        else:
            if use_dot and line.startswith('..'):
                line = line[1:]
            current_value.append(line.lstrip())

    if current_key:
        record[current_key] = '\n'.join(current_value).rstrip()

    record["__field_order__"] = field_order

    return record


def read_records(input: TextIO, use_dot: bool = False) -> list[dict[str, str]]:
    """Read records from the input file."""
    records = []
    current_record = []

    def add_record():
        nonlocal current_record
        record = parse_record(current_record, use_dot)
        records.append(record)
        current_record = []

    for line in input:
        if line.rstrip("\n") == "":
            if current_record:
                add_record()
        else:
            current_record.append(line)

    if current_record:
        add_record()

    return records


def write_record(output: TextIO, record: dict[str, str], indent: str = '\t', use_dot: bool = False):
    """Write a single record to the output file."""
    field_order = record.get("__field_order__")
    if field_order is None:
        field_order = list(record.keys())

    for key in field_order + sorted(k for k in record if k not in field_order):
        if not key in record or key == "__field_order__":
            continue
        value = record[key]
        lines = value.split('\n')
        output.write(f"{key}: {lines[0]}\n")
        for line in lines[1:]:
            if use_dot and not line.strip():
                output.write(".\n")
            else:
                output.write(f"{indent}{line}\n")

    output.write("\n")


def write_records(output: TextIO, records: list[dict[str, str]], indent: str = '\t', use_dot: bool = False):
    """Write records to the output file."""
    for record in records:
        write_record(output, record, indent, use_dot)


def process_records(
    input: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    indent: str = '\t',
    use_dot: bool = False,
    append: bool = False
) -> None:
    """
    Read records from input, process them, and write to output.
    """
    records = read_records(input, use_dot)
    write_records(output, records, indent, use_dot)


def setup_args(arg):
    """Set up command-line arguments."""
    arg('-I', '--indent', help='Indentation string for multi-line values')
    arg('-D', '--dot', help='Use dots for blank lines in multi-line values', action='store_true', dest='use_dot')
    arg('--append', help='Append to the output file instead of overwriting', action='store_true')


if __name__ == "__main__":
    main.go(process_records, setup_args)
