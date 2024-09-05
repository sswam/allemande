#!/usr/bin/env python3

import sys
import logging

logger = logging.getLogger(__name__)

class InvalidTimeFormatError(Exception):
    pass

def subtract_times(time1: str, time2: str) -> str:
    """
    Subtracts two 24-hour format times and returns the result in 24-hour format.
    It can accept times greater than 23:59, e.g. 25:30.

    Args:
        time1 (str): The first time in "HH:MM" format.
        time2 (str): The second time in "HH:MM" format.

    Returns:
        str: The difference in "HH:MM" format.

    Raises:
        InvalidTimeFormatError: If any input time is not in HH:MM format.
    """
    try:
        h1, m1 = map(int, time1.split(':'))
        h2, m2 = map(int, time2.split(':'))
    except ValueError:
        raise InvalidTimeFormatError("Invalid time format")

    t1 = h1 * 60 + m1
    t2 = h2 * 60 + m2

    diff = t1 - t2

    if diff < 0:
        raise ValueError("Time difference is negative")

    hours, minutes = divmod(diff, 60)
    return f"{hours:02}:{minutes:02}"

def main():
    if len(sys.argv) != 3:
        raise ValueError("Usage: python3 subtract_time.py <HH:MM> <HH:MM>")
        return

    time1 = sys.argv[1]
    time2 = sys.argv[2]

    result = subtract_times(time1, time2)
    print(result)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(e)
        sys.exit(1)
