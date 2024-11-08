#!/usr/bin/env python3-allemande

"""
This module describes an interval in seconds.

See also python lib: humanize
e.g. desc = humanize.precisedelta(seconds)
e.g. desc = humanize.precisedelta(datetime.timedelta(seconds=seconds))
This script is kept because it works as a bash function and should be lighter than running python.
"""

import sys
from typing import TextIO
from argh import arg

from ally import main

__version__ = "0.1.2"

logger = main.get_logger()


@arg("seconds", type=int, help="Interval in seconds")
@arg("-s", "--short", help="Use short output format")
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


if __name__ == "__main__":
    main.run(describe_interval)
