#!/usr/bin/env python3

import sys
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class InvalidTimeFormatError(Exception):
    pass

def subtract_times(time1: str, time2: str) -> str:
    """
    Subtracts two 24-hour format times and returns the result in 24-hour format.

    Args:
        time1 (str): The first time in "HH:MM" format.
        time2 (str): The second time in "HH:MM" format.

    Returns:
        str: The difference in "HH:MM" format.
    """
    format_str = "%H:%M"
    try:
        t1 = datetime.strptime(time1, format_str)
        t2 = datetime.strptime(time2, format_str)
    except ValueError as ve:
        raise InvalidTimeFormatError(f"Invalid time format: {ve}")

    tdelta = timedelta(hours=t1.hour, minutes=t1.minute) - timedelta(hours=t2.hour, minutes=t2.minute)
    
    if tdelta.days < 0:
        tdelta = abs(timedelta(hours=24) + tdelta)
    
    hours, remainder = divmod(tdelta.seconds, 3600)
    minutes = remainder // 60

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
