#!/usr/bin/env python3-allemande
# create-relative-symlink.py: create a relative symlink

import os
from pathlib import Path
import argh

## Example usage:
#src_abs_path = "/absolute/path/to/source/file.txt"
#dst_abs_path = "/absolute/path/to/destination/link.txt"
#
#create_relative_symlink(src_abs_path, dst_abs_path)

@argh.arg('--directory', '-d', help="Create a relative symlink in the given directory")
def create_relative_symlink(src_abs_path, dst_abs_path, directory=False, force=False):
    src = Path(src_abs_path)
    dst = Path(dst_abs_path)

    # relative to cwd, don't resolve though
    cwd = Path.cwd()
    src = cwd/src
    dst = cwd/dst

    if directory:
        dst = dst/src.name

    # Make sure the source exists and is not a directory
    if not src.exists() or src.is_dir():
        raise ValueError("Source must be an existing file")

    # Create the destination directory if it doesn't exist
    dst.parent.mkdir(parents=True, exist_ok=True)

    # Calculate the relative path from the destination to the source
    rel_path = os.path.relpath(src, dst.parent)

    if force:
        dst.unlink(missing_ok=True)

    # Create the relative symlink
    dst.symlink_to(rel_path)

if __name__ == '__main__':
    argh.dispatch_command(create_relative_symlink)
