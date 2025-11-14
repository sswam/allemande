#!/usr/bin/env python3-allemande

import sys
import os
from typing import TextIO
from pathlib import Path
from datetime import datetime, timedelta

import records

from ally import main, logs, util

__version__ = "0.1.2"

logger = logs.get_logger()


# an analysis dataclass, for analyze_user_activity return type:

import dataclasses

@dataclasses.dataclass
class UserInfo:
    """Analysis of user activity."""
    is_new: bool
    is_old: bool
    is_inactive: bool
    is_nsfw: bool


def analyze_user_activity(rec, now) -> UserInfo:
    """
    Determine if user is new (under 1 month since btime) or inactive (no mtime in over 1 month)

    Logic:
    - New: now - btime < 15 days
    - Old: now - btime > 30 days
    - Inactive: now - mtime > 30 days and not new
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

    days_30 = timedelta(days=30)

    is_new = now - btime < timedelta(days=15)
    is_old = now - btime > timedelta(days=30)
    is_inactive = now - mtime > timedelta(days=30) and not is_new
    is_nsfw = bool(int(rec.get("nsfw", "1")))

    return UserInfo(is_new=is_new, is_old=is_old, is_inactive=is_inactive, is_nsfw=is_nsfw)


def process_records(
    input: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    indent: str = '\t',
    use_dot: bool = False,
    append: bool = False
) -> None:
    """
    Read records from input, process them, and write to output.
    """
    recs = records.read_records(input, use_dot)
    nag_dir_path = "../../../../adm/nag/active"
    users_dir = os.environ["ALLEMANDE_USERS"]
    now = datetime.now()

    for rec in recs:
        support = rec.get("support")
        nag = rec.get("nag")

        try:
            user_info = analyze_user_activity(rec, now)
        except ValueError as e:
            logger.error("Error analyzing user %s: %s", rec['name'], e)
            continue

        if nag == "no":
            nag_file = None
        elif support in ["family", "friend"]:
            nag_file = "nag-friend.html"
        elif support:
            nag_file = "nag-supporter.html"
        elif user_info.is_new:
            nag_file = "nag-new.html"
        elif user_info.is_inactive:
            nag_file = "nag-inactive.html"
        elif user_info.is_old:
            nag_file = "nag-hiki-stubborn.html"
        elif user_info.is_nsfw:
            nag_file = "nag-hiki-nsfw.html"
        else:
            nag_file = "nag-hiki-sfw.html"

        user_nag_file = Path(f"{users_dir}/{rec['name']}/nag.html")

        if not nag_file:
            user_nag_file.unlink(missing_ok=True)
            user_nag_file.touch()
            print(rec["name"], "", support or "", "", sep="\t")
            continue

        exists = user_nag_file.exists()
        is_symlink = exists and user_nag_file.is_symlink()
        unchanged = is_symlink and str(user_nag_file.readlink()) == f"{nag_dir_path}/{nag_file}"

        logger.debug("Processing user %s: nag=%s, support=%s, nag_file=%s, exists=%s, is_symlink=%s, unchanged=%s", rec['name'], nag, support, nag_file, exists, is_symlink, unchanged)

        if exists and not is_symlink:
            content = user_nag_file.read_text().rstrip()
            print(rec["name"], "", support or "", content, sep="\t")
            continue
        if unchanged:
            continue
        if is_symlink:
            os.unlink(f"{users_dir}/{rec['name']}/nag.html")

        os.symlink(f"{nag_dir_path}/{nag_file}", f"{users_dir}/{rec['name']}/nag.html")

        print(rec["name"], nag_file, support or "", sep="\t")

    # recs = [rec for rec in recs if rec.get("support")]
    # records.write_records(output, recs, indent, use_dot)


def setup_args(arg):
    """Set up command-line arguments."""

if __name__ == "__main__":
    main.go(process_records, setup_args)
