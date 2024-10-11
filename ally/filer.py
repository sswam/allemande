""" File-related utility functions """

import os
import shutil
import time
import mimetypes
from pathlib import Path

from ally import logs


def resource(path: str) -> Path:
    """Get a Path object relative to ALLEMANDE_HOME"""
    return Path(os.environ["ALLEMANDE_HOME"], path)


def find_in_path(file, resolve=True):
    """
    Find a file in the system PATH,
    and resolve symlinks by default.

    Args:
        file (str): The name of the file to find.

    Returns:
        str: The full path to the file if found.

    Raises:
        FileNotFoundError: If the file is not found in PATH.
    """
    for dir in os.environ["PATH"].split(os.pathsep):
        full_path = Path(dir) / file
        if resolve:
            full_path = full_path.resolve()
        if full_path.is_file():
            return str(full_path)
    raise FileNotFoundError(f"{file} (in $PATH)")


def is_binary(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type and not mime_type.startswith("text")


def file_empty(filepath, check_exists=False):
    if not os.path.exists(filepath):
    	return True
    if not os.path.isfile(filepath):
    	return False
    size = os.path.getsize(filepath) 
    if size == 0:
    	return True
    if size == 1 and open(filepath).read(1) == '\n':
    	return True
    return False


def backup(file):
    backup_file = file + "~"

    # Check if backup file exists, and move it to rubbish if it does
    if os.path.exists(backup_file):
        move_to_rubbish(backup_file)

    # Copy the file to create a backup, overwriting if it exists
    shutil.copy2(file, backup_file)


def mount_point(path="."):
    path = os.path.abspath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    return path


def generate_unique_name(parent, basename):
    """
    Generate a unique name for a file in the specified directory.
    """
    while True:
        timestamp = int(time.time() * 1e9)
        new_name = f"{basename}_{timestamp}_{os.getpid()}"
        full_path = os.path.join(parent, new_name)
        if not os.path.exists(full_path):
            return full_path
