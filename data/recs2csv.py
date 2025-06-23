#!/usr/bin/env python3

"""
Convert record-like input to CSV format.
"""

import csv
from collections import defaultdict
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.2"

logger = logs.get_logger()


def parse_records(istream: TextIO, sort: bool = False) -> tuple[list[str], list[dict[str, str]]]:
    """Parse input records into fields and data."""
    fields: list[str] = []
    field_counts: dict[str, int] = defaultdict(int)
    records: list[dict[str, str]] = []
    current_rec: dict[str, str] = {}
    last_key: str | None = None

    n = 0

    for line in istream:
        n += 1
        line = line.rstrip("\n")
        if not line:
            if current_rec:
                records.append(current_rec)
                current_rec = {}
                last_key = None
            continue

        if line.startswith("\t") and last_key is not None:
            # Continuation of previous value
            current_rec[last_key] += "\n" + line[1:]
            continue

        try:
            key, value = line.split(":\t", 1)
        except ValueError:
            logger.warning(f"Skipping malformed line: {n}:{line!r}")
            continue

        if key not in current_rec:
            current_rec[key] = value
        else:
            current_rec[key] = f"{current_rec[key]}\n{value}"

        last_key = key
        if key not in field_counts:
            fields.append(key)
        field_counts[key] += 1

    if current_rec:
        records.append(current_rec)

    if sort:
        fields.sort(key=lambda x: field_counts[x], reverse=True)

    return fields, records


def write_csv(
    fields: list[str],
    records: list[dict[str, str]],
    ostream: TextIO,
    delimiter: str = ",",
) -> None:
    """Write records to CSV format."""
    writer = csv.writer(ostream, delimiter=delimiter, quoting=csv.QUOTE_ALL)
    writer.writerow(fields)
    for record in records:
        row = [record.get(field, "") for field in fields]
        writer.writerow(row)


def process_records(
    istream: TextIO,
    ostream: TextIO,
    tsv: bool = False,
    ssv: bool = False,
    sort: bool = False,
) -> None:
    """Process records from input and write to CSV output."""
    delimiter = "\t" if tsv else ";" if ssv else ","
    fields, records = parse_records(istream, sort)
    write_csv(fields, records, ostream, delimiter)


def setup_args(arg):
    """Set up command-line arguments."""
    arg("-t", "--tsv", action="store_true", help="output as TSV")
    arg("-s", "--ssv", action="store_true", help="output as semicolon-separated values")
    arg("-S", "--sort", action="store_true", help="sort fields by frequency (default: no sort)")


if __name__ == "__main__":
    main.go(process_records, setup_args)
