#!/usr/bin/env python3-allemande

"""
Apply a nag file to users based on their activity and support status.
Reads user records from stdin, symlinks appropriate nag files into user directories,
and writes a summary to stdout.
"""

import dataclasses
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import TextIO
import os

import records

from ally import main, logs, util

__version__ = "0.1.7"

logger = logs.get_logger()


USER_PUBLIC_POSTS_MIN_COUNT = 20
USER_PUBLIC_POSTS_MIN_FRACTION = 0.1


@dataclasses.dataclass
class UserInfo:
    """Analysis of user activity."""
    is_new: bool
    is_old: bool
    is_inactive: bool
    is_nsfw: bool
    is_public_supporter: bool


def analyze_user_activity(rec: dict, now: datetime) -> UserInfo:
    """
    Determine if user is new (under 1 month since btime) or inactive (no mtime in over 2 months)

    Logic:
    - New: now - btime < 30 days
    - Inactive: now - mtime > 180 days and not new

    NOTE: currently different thresholds compared to nag script
    """
    btime_str = rec.get("btime")
    mtime_str = rec.get("mtime")

    if not btime_str:
        raise ValueError(f"User {rec['name']} missing btime")

    if not mtime_str:
        logger.error("WARNING: User %s missing mtime", rec['name'])
        mtime_str = "1970-01-01 00:00:00"

    btime = util.datetime_parse(btime_str)
    mtime = util.datetime_parse(mtime_str)

    is_new = now - btime < timedelta(days=30)
    is_old = now - btime > timedelta(days=60)  # not used here
    is_inactive = now - mtime > timedelta(days=180) and not is_new

    # Updated nsfw check: >0 nsfw posts indicates nsfw user
    nsfw_posts = int(rec.get("nsfw", 0))
    is_nsfw = nsfw_posts > 0 or bool(int(rec.get("is_nsfw", "1")))

    # Check for public supporter: >10% public posts
    public_posts = int(rec.get("public", 0))
    private_posts = int(rec.get("private", 0))
    total_posts = public_posts + private_posts
    public_ratio = public_posts / total_posts if total_posts > 0 else 0.0
    is_public_supporter = public_posts >= USER_PUBLIC_POSTS_MIN_COUNT and public_ratio >= USER_PUBLIC_POSTS_MIN_FRACTION

    return UserInfo(is_new=is_new, is_old=is_old, is_inactive=is_inactive, is_nsfw=is_nsfw, is_public_supporter=is_public_supporter)


def process_single_record(
    rec: dict,
    now: datetime,
    nag_dir: Path,
    users_dir: Path,
    no_act: bool = False,
) -> None:
    """
    Process a single user record, list to stdout if they should be removed.
    """
    support = rec.get("support")
    # nag = rec.get("nag")

    try:
        user_info = analyze_user_activity(rec, now)
    except ValueError as e:
        logger.error("Error analyzing user %s: %s", rec['name'], e)
        return

    if support:
        return

    if user_info.is_new:
        return

    if not user_info.is_inactive:
        return

    print(rec["name"])


def process_records(
    input: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    indent: str = '\t',
    use_dot: bool = False,
    append: bool = False,
) -> None:
    """
    Read records from input, process them, and write to output.
    """
    recs = records.read_records(input, use_dot)
    allemande_home = os.environ["ALLEMANDE_HOME"]
    allemande_users = os.environ["ALLEMANDE_USERS"]

    # Convert to absolute paths
    users_dir = Path(allemande_users).resolve()
    nag_dir = Path(allemande_home) / "adm" / "nag" / "active"

    now = datetime.now()

    for rec in recs:
        process_single_record(rec, now, nag_dir, users_dir)


def setup_args(arg):
    """Set up command-line arguments."""
    # arg("-n", "--no_act", help="Dry run, do not apply changes", action="store_true")


if __name__ == "__main__":
    main.go(process_records, setup_args)

# TODO typing throughout
