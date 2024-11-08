#!/usr/bin/env python3-allemande

"""
rec.py - A module to read, write, and append records in a specific file format.

This module provides functions to handle a record file format with key-value pairs,
supporting multi-line strings and optional field order preservation.

Usage as a module:
    from rec import read_records, write_records, append_records
"""

import sys
import logging
from typing import List, Dict, TextIO, Optional, Tuple

from argh import arg

from ally import main

__version__ = "1.0.1"

logger = main.get_logger()


def parse_record(lines: List[str], use_dot: bool = False) -> Tuple[Dict[str, str], List[str]]:
    """Parse a single record from a list of lines."""
    record = {}
    field_order = []
    current_key = None
    current_value = []

    for line in lines:
        line = line.rstrip()
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

    return record, field_order


def read_records(input: TextIO, use_dot: bool = False) -> Tuple[List[Dict[str, str]], List[List[str]]]:
    """Read records from the input file."""
    records = []
    all_field_orders = []
    current_record = []

    for line in input:
        if line.strip() == "":
            if current_record:
                record, field_order = parse_record(current_record, use_dot)
                records.append(record)
                all_field_orders.append(field_order)
                current_record = []
        else:
            current_record.append(line)

    if current_record:
        record, field_order = parse_record(current_record, use_dot)
        records.append(record)
        all_field_orders.append(field_order)

    return records, all_field_orders


def write_record(output: TextIO, record: Dict[str, str], field_order: Optional[List[str]] = None, indent: str = '\t', use_dot: bool = False):
    """Write a single record to the output file."""
    if field_order is None:
        field_order = list(record.keys())

    for key in field_order:
        if key in record:
            value = record[key]
            output.write(f"{key}: {value.split('\n')[0]}\n")
            for line in value.split('\n')[1:]:
                if use_dot and not line.strip():
                    output.write(".\n")
                else:
                    output.write(f"{indent}{line}\n")

    output.write("\n")


def write_records(output: TextIO, records: List[Dict[str, str]], field_orders: Optional[List[List[str]]] = None, indent: str = '\t', use_dot: bool = False):
    """Write records to the output file."""
    if field_orders is None:
        field_orders = [None] * len(records)

    for record, field_order in zip(records, field_orders):
        write_record(output, record, field_order, indent, use_dot)


@arg('-I', '--indent', help='Indentation string for multi-line values (default: tab)')
@arg('-D', '--dot', help='Use dots for blank lines in multi-line values', action='store_true', dest='use_dot')
@arg('--append', help='Append to the output file instead of overwriting', action='store_true')
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
    records, field_orders = read_records(input, use_dot)
    write_records(output, records, field_orders, indent, use_dot)


if __name__ == "__main__":
    main.run(process_records)
