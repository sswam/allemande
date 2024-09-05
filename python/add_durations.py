#!/usr/bin/env python3

import sys
import logging

logger = logging.getLogger(__name__)

class InvalidTimeFormatError(Exception):
    pass

def add_durations(*times: str) -> str:
    """
    Adds multiple time durations in HH:MM format.
    It can accept durations and totals greater than 23:59, e.g. 25:30.

    Args:
        *times: Variable number of time strings in HH:MM format.

    Returns:
        Sum of durations as a string in HH:MM format.

    Raises:
        InvalidTimeFormatError: If any input time is not in HH:MM format.
    """
    total_minutes = 0

    for time in times:
        try:
            hours, minutes = map(int, time.split(':'))
            total_minutes += hours * 60 + minutes
        except ValueError:
            raise InvalidTimeFormatError(f"Invalid time format: {time}")

    hours, minutes = divmod(total_minutes, 60)

    return f"{hours:02}:{minutes:02}"

def main():
    if len(sys.argv) < 2:
        raise ValueError("Usage: python3 add_durations.py <HH:MM> <HH:MM> ...")

    result = add_durations(*sys.argv[1:])
    print(result)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(e)
        sys.exit(1)
