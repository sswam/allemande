#!/usr/bin/env python3

import sys
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class InvalidTimeFormatError(Exception):
    pass

def add_durations(*times: str) -> str:
    format_str = "%H:%M"
    total_delta = timedelta()
    
    for time in times:
        try:
            t = datetime.strptime(time, format_str)
            total_delta += timedelta(hours=t.hour, minutes=t.minute)
        except ValueError as ve:
            raise InvalidTimeFormatError(f"Invalid time format: {ve}")
    
    hours, remainder = divmod(total_delta.seconds, 3600)
    minutes = remainder // 60

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
