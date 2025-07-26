#!/usr/bin/env python3-allemande

"""
Process webchat user records and identify active or inactive users based on
status, birth time, and modification time thresholds.
"""

import sys
import logging
from datetime import datetime, timedelta
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


def parse_date(date_str: str) -> datetime | None:
    """Parse date string in YYYY-MM-DD HH:MM:SS format."""
    if not date_str:
        return None
    return datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S")


def is_active(
    record: dict[str, str],
    inactive_days: int,
) -> bool:
    """Check if a user is active."""
    now = datetime.now()

    btime = parse_date(record.get("btime", ""))
    if not btime or (now - btime) < timedelta(days=inactive_days):
        return True

    mtime = parse_date(record.get("mtime", ""))
    if mtime and (now - mtime) < timedelta(days=inactive_days):
        return True

    return False


def process_records(
    istream: TextIO,
    ostream: TextIO,
    days: int = 28,
    active: bool = False,
    inactive: bool = False,
) -> None:
    """Process user records and output inactive users."""
    fields = [
        "name",
        "status",
        "btime",
        "mtime",
        "room",
        "count",
        "email",
        "reddit",
        "discord",
        "facebook",
        "contact",
        "notes",
    ]

    if not active and not inactive:
        active = inactive = True

    ostream.write("\t".join(["active"] + fields) + "\n")

    current_record: dict[str, str] = {}

    def process_record():
        if not current_record:
            return
        user_active = is_active(current_record, days)
        ACTIVE = "ACTIVE" if user_active else "INACTIVE"
        if user_active and active or not user_active and inactive:
            values = [ACTIVE] + [current_record.get(field, "") for field in fields]
            ostream.write("\t".join(values) + "\n")

    for line in istream:
        line = line.strip()
        if not line:
            continue

        if line.startswith("#File:"):
            process_record()
            current_record = {}
            continue

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        current_record[key.strip()] = value.strip()

    process_record()


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("--days", "-d", help="days threshold for inactivity")
    arg("--active", "-a", help="show only active users", action="store_true")
    arg("--inactive", "-i", help="show only inactive users", action="store_true")


if __name__ == "__main__":
    main.go(process_records, setup_args)
