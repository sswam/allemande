#!/usr/bin/env python3-allemande

"""
Shows git commit activity per day for the last n days.
"""

import sys
import os
import subprocess
import datetime
from typing import TextIO
import re

from ally import main, logs, geput  # type: ignore

__version__ = "0.1.7"

logger = logs.get_logger()


def run_git_command(command: list[str]) -> str:
    """Run a git command and return the output."""
    try:
        return subprocess.check_output(["git"] + command, universal_newlines=True).strip()
    except subprocess.CalledProcessError as exc:
        raise Exception("Error running git command") from exc


def is_git_repository() -> bool:
    """Check if the current directory is a git repository."""
    try:
        run_git_command(["rev-parse", "--is-inside-work-tree"])
        return True
    except Exception:
        return False


def get_commit_activity(
    days: int, count_loc: bool, count_added_changed: bool
) -> list[tuple[str, int, str, str]]:
    """Get commit activity for the specified number of days."""
    activity = []
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days - 1)

    for date in (start_date + datetime.timedelta(days=d) for d in range(days)):
        date_str = date.isoformat() + " " + date.strftime("%a")
        count = len(
            run_git_command(
                [
                    "log",
                    "--all",
                    "--format=%cd",
                    "--date=short",
                    f"--before={date_str} 23:59:59",
                    f"--after={date_str} 00:00:00",
                ]
            ).splitlines()
        )

        loc = ""
        added_changed = ""

        if count_loc or count_added_changed:
            numstat = run_git_command(
                [
                    "log",
                    "--all",
                    f"--before={date_str} 23:59:59",
                    f"--after={date_str} 00:00:00",
                    "--numstat",
                ]
            )
            if count_loc:
                loc_sum = sum(
                    int(line.split()[0]) + int(line.split()[1])
                    for line in numstat.splitlines()
                    if len(line.split()) >= 2
                    and line.split()[0].isdigit()
                    and line.split()[1].isdigit()
                )
                loc = "999999+" if loc_sum > 999999 else str(loc_sum)
            if count_added_changed:
                added_sum = sum(
                    int(line.split()[0])
                    for line in numstat.splitlines()
                    if len(line.split()) >= 1 and line.split()[0].isdigit()
                )
                added_changed = "999999+" if added_sum > 999999 else str(added_sum)

        activity.append((date_str, count, loc, added_changed))

    return activity


def show_activity(
    days: int,
    put: geput.Put,
    repo_path: str = "",
    count_loc: bool = False,
    count_added_changed: bool = False,
    summary: bool = False,
) -> None:
    """
    Shows git commit activity per day for the last n days.
    """
    print = geput.print(put)
    # Validate inputs
    if days <= 0:
        raise ValueError(f"Invalid number of days: {days}")

    # Change to the repository directory if specified
    if repo_path:
        if not os.path.isdir(repo_path):
            raise ValueError(f"Repository path does not exist: {repo_path}")
        os.chdir(repo_path)

    # Check if current directory is a git repository
    if not is_git_repository():
        raise ValueError("Not a git repository")

    # Get commit activity
    activity_data = get_commit_activity(days, count_loc, count_added_changed)

    headers = ["Date", "Commits"]
    if count_loc:
        headers.append("LOC")
    if count_added_changed:
        headers.append("Added/Changed")
    if summary:
        headers.append("Summary")
    fmt = "{:<10}\t" * (len(headers) - 1) + "{}"
    print(fmt.format(*headers))
    for date, count, loc, added_changed in activity_data:
        row = [date, str(count)]
        if count_loc:
            row.append(loc)
        if count_added_changed:
            row.append(added_changed)
        if summary:
            git_log = run_git_command(
                [
                    "log",
                    "--all",
                    f"--before={date} 23:59:59",
                    f"--after={date} 00:00:00",
                    "--oneline",
                ]
            )
            git_log = "\n".join([re.sub(r"^\S+ ", "", line) for line in git_log.splitlines()])
            summary_output = subprocess.check_output(
                [
                    "summary",
                    "-m=",
                    "List all projects worked on in order of importance or scale of changes. Include tasks if psosible. Absolutely as compact as possible, no wasted words, does not need to be grammatical. All in one line / paragraph, but it may be as long as necessary.",
                ],
                input=git_log,
                universal_newlines=True,
                text=True,
            ).strip()
            row.append(summary_output)
        print(fmt.format(*row))


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("days", help="number of days to show", type=int)
    arg("-r", "--repo-path", help="path to git repository")
    arg("-l", "--count-loc", help="count lines of code", action="store_true")
    arg("-a", "--count-added-changed", help="count only added/changed lines", action="store_true")
    arg("-s", "--summary", help="summarize git log for each day", action="store_true")


if __name__ == "__main__":
    main.go(show_activity, setup_args)
