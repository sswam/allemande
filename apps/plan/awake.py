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
from typing import TextIO
import subprocess

from argh import arg
import sh

from ally import main

__version__ = "0.2.0"

logger = main.get_logger()

CHECK_INTERVAL = 60  # 1 minute
DEFAULT_SLEEP_THRESHOLD = 6 * 3600  # 6 hours
DEFAULT_AWAKE_WARNING = 12 * 3600  # 12 hours
WARN_INTERVAL = 3600  # 1 hour
LOG_FILE = "~/.awake.log"


def check_xprintidle():
    """Check if xprintidle is installed."""
    try:
        sh.which("xprintidle")
    except sh.ErrorReturnCode:
        logger.error("Error: xprintidle is not installed. Please install it first.")
        sys.exit(1)


def get_idle_time():
    """Get the current idle time in seconds."""
    return float(sh.xprintidle()) / 1000


def log_activity(log_file: str, status: str, timestamp: float):
    """Log the current activity."""
    with open(log_file, "a") as f:
        f.write(f"{timestamp.isoformat()} - {status.title()}\n")


def estimate_sleep(log_file: str, sleep_threshold: int):
    """Estimate when the user last slept and for how long."""
    with open(log_file, "r") as f:
        lines = f.readlines()

    if not lines:
        return None, None, None

    # TODO need to check Active vs Away

    last_activity = datetime.fromisoformat(lines[-1].split(" - ")[0])
    sleep_start = None
    sleep_end = None

    for i in range(len(lines) - 2, -1, -1):
        current_activity = datetime.fromisoformat(lines[i].split(" - ")[0])
        if (last_activity - current_activity).total_seconds() >= sleep_threshold:
            sleep_end = last_activity
            sleep_start = current_activity
            sleep_duration = sleep_end - sleep_start
            return sleep_start, sleep_end, sleep_duration
        last_activity = current_activity

    return None, None, None


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
def awake_py(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    log_file: str = LOG_FILE,
    sleep_threshold: int = DEFAULT_SLEEP_THRESHOLD,
    no_warn: bool = False,
    awake_warning: int = DEFAULT_AWAKE_WARNING,
):
    """
    Track user activity on X11 and log when awake.
    Estimate sleep duration and provide warnings for extended awake periods.
    """

    check_xprintidle()

    log_file = os.path.expanduser(log_file)
    last_active = datetime.now()
    last_warning = datetime.now() - timedelta(seconds=WARN_INTERVAL)

    logger.info(f"Starting X11 activity tracking. Logging to {log_file}")
    logger.info("Press Ctrl+C to stop.")

    first = True

    while True:
        if not first:
            time.sleep(CHECK_INTERVAL)
        first = False

        now = datetime.now()
        idle_time = get_idle_time()

        if idle_time > CHECK_INTERVAL + 0.5:
            status = "away"
            status_time = now
        else:
            status = "active"
            status_time = now - timedelta(seconds=idle_time)

        logger.debug(f"User seems to be {status}")

        log_status(log_file, status_time, status)

        if status == "away"
            continue

        # TODO estimate_sleep is inefficient, we should keep the DB in memory and assume no one
        # is messing with it, better still check if it was edited since we last loaded it
        sleep_start, sleep_end, sleep_duration = estimate_sleep(log_file, sleep_threshold)
        if not sleep_start:
            logger.debug("No sleep data available.")
            continue

        logger.info(f"Last sleep: {sleep_start}, Duration: {sleep_duration}")

        awake_time = status_time - sleep_end

        logger.info(f"Awake from: {sleep_end}, Duration: {awake_time}")

        if no_warn or awake_time.total_seconds() < awake_warning:
            continue

        if (now - last_warning).total_seconds() < WARN_INTERVAL:
            continue

        message = f"You've been awake for {awake_time.total_seconds() // 3600} hours!"
        send_notification(message)
        last_warning = now


if __name__ == "__main__":
    main.run(awake_py)


# TODO track total time at the computer,
# excluding idle time more than 5 minutes (or configurable): idle_threshold
