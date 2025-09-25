#!/usr/bin/env python3-allemande

import sys
import os
from typing import TextIO
from pathlib import Path

import records

from ally import main, logs

__version__ = "0.1.1"

logger = logs.get_logger()


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
    for rec in recs:
        support = rec.get("support")
        nag = rec.get("nag")
        if nag == "no":
            nag_file = None
        elif support in ["family", "friend"]:
            nag_file = "nag-friend.html"
        elif support:
            nag_file = "nag-supporter.html"
        else:
            nag_file = "nag.html"

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
