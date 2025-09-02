#!/usr/bin/env python3-allemande

import sys
import os
from typing import TextIO

import records

from ally import main

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
    nag_dir_path = "../../../../adm/nag/feedback-ally"
    users_dir = os.environ["ALLEMANDE_USERS"]
    for rec in recs:
        support = rec.get("support")
        nag = rec.get("nag")
        print(rec["name"], support or "", sep="\t")
        if nag == "no":
            nag_file = None
        elif support in ["family", "friend"]:
            nag_file = "nag-friend.html"
        elif support:
            nag_file = "nag-supporter.html"
        else:
            nag_file = "nag.html"
        try:
            os.unlink(f"{users_dir}/{rec['name']}/nag.html")
        except FileNotFoundError:
            pass
        if nag_file:
            os.symlink(f"{nag_dir_path}/{nag_file}", f"{users_dir}/{rec['name']}/nag.html")
    # recs = [rec for rec in recs if rec.get("support")]
    # records.write_records(output, recs, indent, use_dot)


def setup_args(arg):
    """Set up command-line arguments."""

if __name__ == "__main__":
    main.go(process_records, setup_args)
