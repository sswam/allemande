#!/usr/bin/env python3-allemande

"""
CSV reader that handles quoted fields and strips whitespace around unquoted values.
"""

import re
from typing import Iterator, TextIO, Generator
from ally import main, logs
import csv

__version__ = "0.1.4"

logger = logs.get_logger()


class CSVReader:
    """A CSV reader that strips whitespace and handles quoted fields."""

    def __init__(
        self,
        fileobj: TextIO,
        delimiter: str = ",",
        quotechar: str = '"',
        escapechar: str | None = None,
        doublequote: bool = True,
        lineterminator: str = "\n",
    ) -> None:
        """Initialize the CSV reader with a file object and CSV format parameters."""
        self.fileobj = fileobj
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.escapechar = escapechar
        self.doublequote = doublequote
        self.lineterminator = lineterminator
        self.buffer = ""
        self.row: list[str] = []

    def _build_field_pattern(self) -> str:
        """Build the regexp pattern for field matching based on CSV parameters."""
        quote = re.escape(self.quotechar)
        delim = re.escape(self.delimiter)
        lineterm = re.escape(self.lineterminator)
        space = r"[^\S\t]" if self.delimiter == "\t" else r"\s"

        unquoted_empty = rf"{space}*?"
        unquoted_nonempty = rf"{space}*[^{quote}{delim}\s].*?"
        field = rf"{unquoted_empty}|{unquoted_nonempty}"

        if self.quotechar:
            if self.escapechar:
                escape = re.escape(self.escapechar)
                quoted = rf"{space}*{quote}(?:[^{quote}]|{escape}.|{quote}{quote})*{quote}{space}*?"
            elif self.doublequote:
                quoted = rf"{space}*{quote}(?:[^{quote}]|{quote}{quote})*{quote}{space}*?"
            else:
                quoted = rf"{space}*{quote}[^{quote}]*{quote}{space}*"
            field = rf"{quoted}|{field}"

        return rf"({field})({delim}|{lineterm})"

    def _clean_field(self, field: str) -> str:
        """Clean a field by handling quotes and stripping whitespace."""
        field = field.strip()
        if not self.quotechar:
            return field

        quoted = field.startswith(self.quotechar) and field.endswith(self.quotechar)
        if not quoted:
            return field

        field = field[1:-1]
        if self.escapechar:
            field = re.sub(f"{re.escape(self.escapechar)}(.)", r"\1", field)
            if field.endswith(self.escapechar):
                raise ValueError(f"Escape character at end of field: {field!r}")
        elif self.doublequote:
            field = field.replace(self.quotechar * 2, self.quotechar)
        return field

    def process_buffer(self) -> Generator[list[str], None, None]:
        """Process the current buffer and yield complete rows."""
        field_re = re.compile(self._build_field_pattern())
        while match := field_re.match(self.buffer):
            field, sep = match.groups()
            self.buffer = self.buffer[match.end():]
            self.row.append(field)
            if sep == self.lineterminator:
                yield [self._clean_field(field) for field in self.row]
                self.row = []

    def __iter__(self) -> Iterator[list[str]]:
        """Iterate over rows in the CSV file."""
        self.buffer = ""
        self.row = []
        for line in self.fileobj:
            eof = not line.endswith("\n")
            if eof and not line.endswith(self.lineterminator):
                line += "\n"
            self.buffer += line
            yield from self.process_buffer()

        if self.buffer:
            raise ValueError(f"Incomplete CSV row at end of file: {self.buffer!r}")

    def __next__(self) -> list[str]:
        """Get the next row from the CSV file."""
        return next(iter(self))


def reader(
    fileobj: TextIO,
    delimiter: str = ",",
    quotechar: str = '"',
    escapechar: str | None = None,
    doublequote: bool = True,
    lineterminator: str = "\n",
) -> Iterator[list[str]]:
    """Create a CSV reader that strips whitespace and handles quoted fields."""
    return CSVReader(
        fileobj,
        delimiter=delimiter,
        quotechar=quotechar,
        escapechar=escapechar,
        doublequote=doublequote,
        lineterminator=lineterminator,
    )


def tidy_csv(
    istream: TextIO,
    ostream: TextIO,
    delimiter: str = ",",
    quotechar: str = '"',
    escapechar: str | None = None,
    doublequote: bool = True,
    lineterminator: str = "\n",
) -> None:
    """Read a CSV file and yield cleaned rows."""
    opts = {
        "delimiter": delimiter,
        "quotechar": quotechar,
        "escapechar": escapechar,
        "doublequote": doublequote,
        "lineterminator": lineterminator,
    }
    writer = csv.writer(ostream, **opts)
    for row in reader(istream, **opts):
        writer.writerow(row)


def setup_args(arg):
    arg("-d", "--delimiter", help="Field delimiter")
    arg("-q", "--quotechar", help="Quote character")
    arg("-e", "--escapechar", help="Escape character")
    arg("-D", "--doublequote", help="Doublequote")
    arg("-t", "--lineterminator", help="Line terminator")


if __name__ == "__main__":
    main.go(tidy_csv, setup_args)
