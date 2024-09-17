#!/usr/bin/env python3

"""
hi.py - An minimal example Python module / script to say hello,
"""

import sys
import logging
from typing import TextIO, Optional

from argh import arg

from ally import main

__version__ = "1.0.0"

logger = logging.getLogger(__name__)


@arg("--name", help="name to be greeted")
def hello(
    ostream: TextIO = sys.stdout,
    name: str = "World",
    log_level: Optional[str] = None,
) -> None:
    """
    A minimal example Python module / script to say hello,
    """
    main.setup_logging(log_level)

    print(f"Hello, {name}", file=ostream)


if __name__ == "__main__":
    main.run(hello)
