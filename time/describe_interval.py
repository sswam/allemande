#!/usr/bin/env python3-allemande

"""
This module describes an interval in seconds.

See also python lib: humanize
"""

import sys
from typing import TextIO
from argh import arg

from ally import main, logs

__version__ = "0.1.2"

logger = logs.get_logger()


def describe_interval(seconds: int, short: bool = False) -> str:
    """Describe an interval in seconds."""
    if seconds >= 86400:
        n, unit = divmod(seconds, 86400)
        unit = "day"
    elif seconds >= 3600:
        n, unit = divmod(seconds, 3600)
        unit = "hour"
    elif seconds >= 60:
        n, unit = divmod(seconds, 60)
        unit = "minute"
    else:
        n, unit = seconds, "second"

    if n > 1:
        unit += "s"

    if short:
        return f"{n}{unit[0]}"
    return f"{n} {unit}"


def setup_args(arg):
    arg("seconds", type=int, help="Interval in seconds")
    arg("-s", "--short", action='store_true', help="Use short output format")


if __name__ == "__main__":
    main.go(describe_interval, setup_args)
