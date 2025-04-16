#!/usr/bin/env python3

"""Utility to update paths in a Python virtual environment after moving it"""

# XXX This does not work yet, or at least the tests do not pass yet.

import os
import re
import shutil
import argparse

__VERSION__ = "0.1.4"


def verify_venv(venv: str) -> bool:
    """Verify that the virtual environment exists and contains required files"""
    if not os.path.isdir(venv):
        print(f"The virtual environment {venv} does not exist")
        return False
    if not os.path.isdir(os.path.join(venv, "bin")):
        print(f"The virtual environment {venv} does not contain a bin directory")
        return False
    if not os.path.isfile(os.path.join(venv, "bin", "activate")):
        print(f"The virtual environment {venv} does not contain a bin/activate file")
        return False
    return True


def remove_pycache_dirs(root: str) -> None:
    """Remove all __pycache__ directories under the given root"""
    for dirpath, dirnames, _ in os.walk(root):
        for d in dirnames:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(dirpath, d))


def venv_move(venv: str, remove_pycache: bool = True, yes: bool = False) -> None:
    """Update paths in a virtual environment after it has been moved

    Args:
        venv: Path to the virtual environment
        remove_pycache: Whether to remove __pycache__ directories
        yes: Skip confirmation prompts
    """
    if not verify_venv(venv):
        raise ValueError("Invalid virtual environment")

    venv = os.path.abspath(venv)
    venv_name = os.path.basename(venv)

    if remove_pycache:
        remove_pycache_dirs(venv)

    # Find and replace old path with new path
    activate_path = os.path.join(venv, "bin", "activate")
    with open(activate_path, "r", encoding="utf-8") as f:
        activate_script = f.read()

    match = re.search(r'VIRTUAL_ENV=["\'](.*?)["\']', activate_script)
    if not match:
        raise ValueError("Could not find VIRTUAL_ENV in activate script")
    old_path = match.group(1)
    new_path = os.path.abspath(venv)

    if old_path == new_path:
        print(f"venv paths are already set correctly to {new_path}")
        return

    matching_files = []
    for root, _, files in os.walk(venv):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext not in [".py", ".sh"]:
                continue
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                file_text = f.read()
            if old_path in file_text:
                print(file_path)
                matching_files.append(file_path)

    if not yes:
        response = input(f"Replace {old_path} with {new_path} in the above files? [y/n] ")
        if response != "y":
            return

    for file_path in matching_files:
        with open(file_path, "r", encoding="utf-8") as f:
            file_text = f.read()
        file_text = file_text.replace(old_path, new_path)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_text)

    # Handle basename replacement in activate files
    old_basename = f"({os.path.basename(old_path)})"
    new_basename = f"({venv_name})"

    basename_files = []
    for file in os.listdir(os.path.join(venv, "bin")):
        if file.startswith("activate"):
            file_path = os.path.join(venv, "bin", file)
            with open(file_path, "r", encoding="utf-8") as f:
                file_text = f.read()
            if old_basename in file_text:
                print(file_path)
                basename_files.append(file_path)

    if basename_files and not yes:
        response = input(f"Replace {old_basename} with {new_basename} in the above files? [y/n] ")
        if response != "y":
            return

    for file_path in basename_files:
        with open(file_path, "r", encoding="utf-8") as f:
            file_text = f.read()
        file_text = file_text.replace(old_basename, new_basename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("venv", help="Path to the virtual environment")
    parser.add_argument("--keep-pycache", action="store_true", help="Do not remove __pycache__ directories")
    parser.add_argument("--yes", action="store_true", help="Do not prompt for confirmation")
    args = parser.parse_args()
    venv_move(args.venv, remove_pycache=not args.keep_pycache, yes=args.yes)
