#!/usr/bin/env python3-allemande

"""
Convert between pounds (lbs) and kilograms (kg).
"""

import sys
import logging
from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


LB_IN_KG = 0.453592


def convert_weight(value: float, reverse: bool = False) -> float:
    """Convert between lbs and kg."""
    if reverse:
        return value / LB_IN_KG
    return value * LB_IN_KG


def lbs(value: float, reverse: bool = False) -> None:
    """Convert weight between pounds and kilograms."""
    if value < 0:
        raise ValueError("Weight cannot be negative")

    result = convert_weight(value, reverse)

    if logs.level() <= logs.INFO:
        if reverse:
            print(f"{value:.2f} kg = {result:.2f} lbs")
        else:
            print(f"{value:.2f} lbs = {result:.2f} kg")
    else:
        print(f"{result:.2f}")


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("value", type=float, help="weight value to convert")
    arg("-r", "--reverse", action="store_true",
        help="convert from kg to lbs instead of lbs to kg")


if __name__ == "__main__":
    main.go(lbs, setup_args)
