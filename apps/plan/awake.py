#!/usr/bin/env python3

"""
Tracks user activity on X11 and logs when the user is awake.
It also provides estimates for sleep duration and wake time.
"""

import os
import sys
import time
from datetime import datetime, timedelta
import subprocess
from dataclasses import dataclass

from ally import main, logs

__version__ = "0.2.8"

logger = logs.get_logger()


# pylint: disable=too-many-instance-attributes
@dataclass
class Config:
    """Configuration for awake tracking."""

    log_file: str
    sleep_threshold: timedelta
    no_warn: bool
    awake_warning: timedelta
    away_threshold: timedelta
    check_interval: timedelta
    warn_interval: timedelta
    test: bool


def check_xprintidle():
    """Check if xprintidle is installed."""
    try:
        subprocess.run(["which", "xprintidle"], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        logger.error("Error: xprintidle is not installed. Please install it first.")
        sys.exit(1)


def get_idle_time() -> timedelta:
    """Get the current idle time."""
    try:
        result = subprocess.run(["xprintidle"], check=True, capture_output=True, text=True)
        return timedelta(milliseconds=int(result.stdout.strip()))
    except subprocess.CalledProcessError as e:
        logger.error("Error running xprintidle: %s", e)
        sys.exit(1)


class ActivityLog:
    """Activity log for tracking user activity."""

    def __init__(self, log_file: str):
        """Initialize the activity log."""
        self.log_file = log_file
        self.activities: list[tuple[datetime, str]] = []
        self.last_modified = 0.0
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
        logger.debug("Loading log from %s", self.log_file)
        self.clear()
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f.readlines():
                line = line.strip()
                if not line:
                    continue
                status_time_str, status = line.split(" - ")
                status_time = datetime.fromisoformat(status_time_str)
                self._add_activity(status_time, status)

    def _add_activity(self, timestamp: datetime, status: str):
        """Add an activity to the internal log."""
        self.activities.append((timestamp, status))

    def add_activity(self, timestamp: datetime, status: str):
        """Add an activity to the internal log and to the log file."""
        self._log_activity(timestamp, status)
        self._add_activity(timestamp, status)

    def _log_activity(self, timestamp: datetime, status: str):
        """Log the current activity."""
        self.load_log()
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp.isoformat()} - {status}\n")
        self.last_modified = os.path.getmtime(self.log_file)

    def find_sleep(self, sleep_threshold: timedelta) -> tuple[datetime | None, datetime | None]:
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

    def total_active_since(self, since: datetime | None) -> timedelta:
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
                too_old = since is not None and timestamp < since
            if (too_old or status == "away") and active_end:
                total_active += active_end - active_start
                active_start = active_end = None
            if too_old:
                break
            if status == "active" and not active_end:
                active_end = timestamp
            if status == "active":
                active_start = timestamp
        if status == "active" and active_end and active_start:
            total_active += active_end - active_start
        return total_active


def format_duration(duration):
    """
    Format a duration to a string with days, hours, and minutes.
    """
    if duration is None:
        return "unknown"

    days, remainder = divmod(duration.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{int(days)} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{int(hours)} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{int(minutes)} minute{'s' if minutes != 1 else ''}")

    if not parts:
        return "less than a minute"

    return ", ".join(parts)


def send_notification(message: str):
    """Send a notification using notify-send."""
    try:
        subprocess.run(
            [
                "notify-send",
                "-u",
                "critical",
                "-t",
                "10000",
                "-i",
                "/usr/share/icons/gnome/48x48/status/appointment-soon.png",
                "Awake Warning",
                message,
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error("Failed to send notification: %s", e)


def process_activity(
    config: Config, activity_log: ActivityLog, now: datetime, idle_time: timedelta
):
    """Process the current activity and log it."""
    status_time = now
    if idle_time < config.check_interval + timedelta(seconds=1):
        status = "active"
        status_time = now - idle_time
    elif idle_time < config.away_threshold:
        status = "inactive"
    else:
        status = "away"

    activity_log.add_activity(status_time, status)
    logger.info("User is %s", status)
    return status


def analyze_activity(config: Config, activity_log: ActivityLog, now: datetime):
    """Analyze the activity log and return sleep and awake durations."""
    sleep_start, sleep_end = activity_log.find_sleep(config.sleep_threshold)
    sleep_duration = sleep_end - sleep_start if sleep_end and sleep_start else None

    awake_start = sleep_end if sleep_end else activity_log.activities[0][0]
    awake_duration = now - awake_start if awake_start else None

    work_duration = activity_log.total_active_since(awake_start)

    return sleep_duration, awake_duration, work_duration


def log_activity_info(sleep_duration, awake_duration, work_duration):
    """Log information about sleep and awake durations."""
    logger.info("Slept for %s", format_duration(sleep_duration))
    logger.info("Awake for %s", format_duration(awake_duration))


def check_and_send_warning(
    config: Config, awake_duration: timedelta, last_warning: datetime, now: datetime
):
    """Check if a warning should be sent and send it if necessary."""
    if config.no_warn or not awake_duration or awake_duration < config.awake_warning:
        return last_warning

    if now - last_warning >= config.warn_interval:
        message = f"You've been awake for {format_duration(awake_duration)}!"
        logger.warning(message)
        send_notification(message)
        return now

    return last_warning


def awake_step(config: Config, activity_log: ActivityLog, last_warning: datetime) -> datetime:
    """Perform a single awake tracking step."""
    now = datetime.now()
    idle_time = get_idle_time()
    logger.debug("Now: %s, Idle time: %s", now, format_duration(idle_time))

    status = process_activity(config, activity_log, now, idle_time)

    if status == "active":
        sleep_duration, awake_duration, work_duration = analyze_activity(config, activity_log, now)
        log_activity_info(sleep_duration, awake_duration, work_duration)
        last_warning = check_and_send_warning(config, awake_duration, last_warning, now)

    return last_warning


def show_current_status(config: Config):
    """Show the current sleep and awake time based on the tail of the logs."""
    activity_log = ActivityLog(config.log_file)
    now = datetime.now()
    sleep_duration, awake_duration, _ = analyze_activity(config, activity_log, now)
    logs.set_log_level("INFO")
    log_activity_info(sleep_duration, awake_duration, None)


# pylint: disable=too-many-arguments, too-many-positional-arguments
def awake(
    log_file: str = "~/.awake.log",
    sleep_threshold: int = 6 * 3600,
    no_warn: bool = False,
    awake_warning: int = 12 * 3600,
    away_threshold: int = 300,
    check_interval: int = 60,
    warn_interval: int = 3600,
    test: bool = False,
    show_status: bool = False,
):
    """
    Track user activity on X11 and log when awake.
    Estimate sleep duration and provide warnings for extended awake periods.
    """
    check_xprintidle()

    config = Config(
        log_file=os.path.expanduser(log_file),
        sleep_threshold=timedelta(seconds=sleep_threshold),
        no_warn=no_warn,
        awake_warning=timedelta(seconds=awake_warning),
        away_threshold=timedelta(seconds=away_threshold),
        check_interval=timedelta(seconds=check_interval),
        warn_interval=timedelta(seconds=warn_interval),
        test=test,
    )

    if show_status:
        show_current_status(config)
        return

    if test:
        logger.info("Running in test mode")
        config.check_interval = timedelta(seconds=10)
        config.warn_interval = timedelta(seconds=30)
        config.sleep_threshold = timedelta(seconds=60)
        config.awake_warning = timedelta(seconds=120)
        config.away_threshold = timedelta(seconds=20)
        config.log_file = "/tmp/awake.log"

    activity_log = ActivityLog(config.log_file)
    last_warning = datetime.now() - config.warn_interval

    logger.info("Starting X11 activity tracking. Logging to %s", config.log_file)
    logger.info("Press Ctrl+C to stop.")

    first = True

    while True:
        if not first:
            delay = config.check_interval.total_seconds()
            seconds_of_day = datetime.now().second + datetime.now().microsecond / 1_000_000
            delay -= seconds_of_day % delay
            if delay <= delay / 2:
                delay += config.check_interval.total_seconds()
            logger.debug("Sleeping for %s seconds", delay)
            time.sleep(delay)
        first = False

        last_warning = awake_step(config, activity_log, last_warning)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("--log-file", help="Path to the log file")
    arg("--sleep-threshold", help="Sleep threshold in seconds", type=int)
    arg("--no-warn", help="Disable awake warnings", action="store_true")
    arg("--awake-warning", help="Awake warning threshold in seconds", type=int)
    arg("--away-threshold", help="Away threshold in seconds", type=int)
    arg("--check-interval", help="Check interval in seconds", type=int)
    arg("--warn-interval", help="Awake warning interval in seconds", type=int)
    arg("--test", help="Run in test mode, with a very compressed time scale", action="store_true")
    arg("-s", "--show-status", help="Show current sleep and awake time", action="store_true")


if __name__ == "__main__":
    main.go(awake, setup_args)
