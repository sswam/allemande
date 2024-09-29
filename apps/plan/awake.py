#!/usr/bin/env python3

"""
This module tracks user activity on X11 and logs when the user is awake.
It also provides estimates for sleep duration and wake time.
"""

import os
import sys
import logging
import time
from datetime import datetime, timedelta
from typing import TextIO, List, Tuple
import subprocess
import humanize

from argh import arg
import sh

from ally import main

__version__ = "0.2.1"

logger = main.get_logger()

DEFAULT_CHECK_INTERVAL = 60  # 1 minute
DEFAULT_SLEEP_THRESHOLD = 6 * 3600  # 6 hours
DEFAULT_AWAKE_WARNING = 12 * 3600  # 12 hours
DEFAULT_WARN_INTERVAL = 3600  # 1 hour
LOG_FILE = "~/.awake.log"
DEFAULT_AWAY_THRESHOLD = 300  # 5 minutes


def check_xprintidle():
    """Check if xprintidle is installed."""
    try:
        sh.which("xprintidle")
    except sh.ErrorReturnCode:
        logger.error("Error: xprintidle is not installed. Please install it first.")
        sys.exit(1)


def get_idle_time() -> timedelta:
    """Get the current idle time."""
    return timedelta(seconds=float(sh.xprintidle()) / 1000)


class ActivityLog:
    """Activity log for tracking user activity."""

    def __init__(self, log_file: str):
        """Initialize the activity log."""
        self.log_file = log_file
        self.activities: List[Tuple[datetime, str]] = []
        self.last_modified = 0
        self.load_log()

    def clear(self):
        """Clear the activity log."""
        self.activities = []

    def load_log(self):
        """Load the activity log from the log file, if it has been modified."""
        if not os.path.exists(self.log_file):
            return
        while True:
            current_modified = os.path.getmtime(self.log_file)
            if current_modified == self.last_modified:
                break
            self._load_log()
            self.last_modified = current_modified

    def _load_log(self):
        """Load the activity log from the log file."""
        logger.debug(f"Loading log from {self.log_file}")
        self.clear()
        with open(self.log_file, "r") as f:
            for line in f.readlines():
                line = line.strip()
                if not line:
                    continue
                status_time_str, status = line.split(" - ")
                status_time = datetime.fromisoformat(status_time_str)
                self._add_activity(status_time, status)

    def _add_activity(self, timestamp: datetime, status: str, log=True):
        """Add an activity to the internal log."""
        self.activities.append((timestamp, status))

    def add_activity(self, timestamp: datetime, status: str):
        """Add an activity to the internal log and to the log file."""
        self._log_activity(timestamp, status)
        self._add_activity(timestamp, status)

    def _log_activity(self, timestamp: datetime, status: str):
        """Log the current activity."""
        self.load_log()
        with open(self.log_file, "a") as f:
            f.write(f"{timestamp.isoformat()} - {status}\n")
        self.last_modified = os.path.getmtime(self.log_file)

    def find_sleep(self, sleep_threshold: timedelta) -> Tuple[datetime, datetime]:
        """Find the last sleep period."""
        if not self.activities:
            return None, None
        sleep_end = self.activities[-1][0]
        i = len(self.activities) - 1
        while i >= 0:
            timestamp, status = self.activities[i]
            if status == "active":
                if sleep_end and sleep_end - timestamp >= sleep_threshold:
                    return timestamp, sleep_end
                sleep_end = timestamp
            i -= 1
        return None, None

    def total_active_since(self, since: datetime|None) -> timedelta:
        """Calculate the total active time since the given timestamp."""
        # looking for spans of active ... inactive ... active
        # or inactive ... active at the start
        total_active = timedelta()
        active_start = active_end = None
        for i in range(len(self.activities) - 1, -2, -1):
            timestamp, status = None, None
            too_old = i == -1
            if not too_old:
                timestamp, status = self.activities[i]
                too_old = since and timestamp < since
            if (too_old or status == "away") and active_end:
                total_active += active_end - active_start
                active_start = active_end = None
            if too_old:
                break
            if status == "active" and not active_end:
                active_end = timestamp
            if status == "active":
                active_start = timestamp
        if status == "active" and active_end:
            total_active += active_end - timestamp
        return total_active


def send_notification(message: str):
    """Send a notification using notify-send."""
    try:
        subprocess.run([
            "notify-send",
            "-u", "critical",
            "-t", "10000",
            "-i", "/usr/share/icons/gnome/48x48/status/appointment-soon.png",
            "Awake Warning",
            message
        ], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to send notification: {e}")


@arg("--log-file", help="Path to the log file", default="~/.awake.log")
@arg("--sleep-threshold", help="Sleep threshold in seconds", type=int, default=DEFAULT_SLEEP_THRESHOLD)
@arg("--no-warn", help="Disable awake warnings", action="store_true")
@arg("--awake-warning", help="Awake warning threshold in seconds", type=int, default=DEFAULT_AWAKE_WARNING)
@arg("--away-threshold", help="Away threshold in seconds", type=int, default=DEFAULT_AWAY_THRESHOLD)
@arg("--check-interval", help="Check interval in seconds", type=int, default=DEFAULT_CHECK_INTERVAL)
@arg("--warn-interval", help="Awake warning interval in seconds", type=int, default=DEFAULT_WARN_INTERVAL)
@arg("--dots", "-d", help="Print a dot for each check", action="store_true")
@arg("--test", help="Run in test mode, with a very compressed time scale", action="store_true")
def awake(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    log_file: str = LOG_FILE,
    sleep_threshold: int = DEFAULT_SLEEP_THRESHOLD,
    no_warn: bool = False,
    awake_warning: int = DEFAULT_AWAKE_WARNING,
    away_threshold: int = DEFAULT_AWAY_THRESHOLD,
    check_interval: int = DEFAULT_CHECK_INTERVAL,
    warn_interval: int = DEFAULT_WARN_INTERVAL,
    dots: bool = True,
    test: bool = False,
):
    """
    Track user activity on X11 and log when awake.
    Estimate sleep duration and provide warnings for extended awake periods.
    """

    check_xprintidle()

    if test:
        logger.info("Running in test mode")
        check_interval = 10
        warn_interval = 30
        sleep_threshold = 60
        awake_warning = 120
        away_threshold = 20
        log_file = "/tmp/awake.log"
        dots = False

    check_interval = timedelta(seconds=check_interval)
    warn_interval = timedelta(seconds=warn_interval)
    sleep_threshold = timedelta(seconds=sleep_threshold)
    awake_warning = timedelta(seconds=awake_warning)
    away_threshold = timedelta(seconds=away_threshold)

    log_file = os.path.expanduser(log_file)
    activity_log = ActivityLog(log_file)
    last_warning = datetime.now() - warn_interval
    last_status = None

    logger.info(f"Starting X11 activity tracking. Logging to {log_file}")
    logger.info("Press Ctrl+C to stop.")

    first = True

    while True:
        if not first:
            delay = check_interval.total_seconds()
            # sync with the clock
            seconds_of_day = datetime.now().second + datetime.now().microsecond / 1_000_000
            delay -= seconds_of_day % delay
            if delay <= delay / 2:
                delay += check_interval.total_seconds()
            logger.debug(f"Sleeping for {delay} seconds")
            time.sleep(delay)
        first = False

        now = datetime.now()
        idle_time = get_idle_time()
        logger.debug(f"Now: {now}, Idle time: {humanize.naturaldelta(idle_time)}")

        status_time = now

        if idle_time < check_interval + timedelta(seconds=1):
            status = "active"
            status_time = now - idle_time
        elif idle_time < away_threshold:
            status = "inactive"
        else:
            status = "away"

        # always log the status, so we can see when the script is not running
        activity_log.add_activity(status_time, status)

        if status == last_status:
            if dots:
                print(".", file=sys.stderr, end="")
            continue

        last_status = status

        if dots:
            print("\n", file=sys.stderr)

        logger.info(f"User is {status}")

        if status != "active":
            continue

        # Main functionality:
        # 1. find previous sleep period
        #   - awake start
        #   - sleep duration
        # 2. current awake duration
        # 3. current work duration (at the computer) since sleep

        sleep_start, sleep_end = activity_log.find_sleep(sleep_threshold)
        sleep_duration = sleep_end - sleep_start if sleep_end else None

        awake_start, awake_end = sleep_end, now
        if not awake_start:
            awake_start = activity_log.activities[0][0]
        awake_duration = awake_end - awake_start if awake_start else None

        work_duration = activity_log.total_active_since(awake_start)

        logger.info(f"Last sleep: {sleep_start}, Duration: {humanize.naturaldelta(sleep_duration)}")
        logger.info(f"Awake from: {awake_start}, Duration: {humanize.naturaldelta(awake_duration)}")
        logger.info(f"Work duration: {humanize.naturaldelta(work_duration)}")

        if no_warn or not awake_duration or awake_duration < awake_warning:
            continue

        if now - last_warning >= warn_interval:
            message = f"You've been awake for {humanize.naturaldelta(awake_duration)}!"
            logger.warning(message)
            send_notification(message)
            last_warning = now


if __name__ == "__main__":
    main.run(awake)
