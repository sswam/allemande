#!/usr/bin/env python3-allemande

"""
This module extracts dependencies from bash or sh scripts, including sourced scripts,
files referenced absolutely, and tools executed.
"""

import sys
import os
import logging
import re
from typing import TextIO, Set, Optional

import shlex
from argh import arg

from ally import main  # type: ignore
from ally.lazy import lazy  # type: ignore

__version__ = "0.1.5"

logger = main.get_logger()

tools_standard = main.load(main.resource("tools/tools_standard.txt"))


def parse_script(content: str) -> Set[str]:
    """Parse the script content and extract dependencies."""
    deps = set()
    lines = content.splitlines()
    cwd = os.getcwd()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Handle redirections before the command
        line = re.sub(r"^[<>].*?(\S+)", r"\1", line)

        try:
            tokens = shlex.split(line, comments=True)
        except ValueError as e:
            logger.warning(f"Failed to parse line: {line}. Error: {e}")
            continue

        if not tokens:
            continue

        # Check for source or . (dot) command
        if tokens[0] in ["source", "."] and len(tokens) > 1:
            sourced_file = os.path.abspath(os.path.expandvars(tokens[1]))
            deps.add(sourced_file)
            logger.debug(f"Added sourced file dependency: {sourced_file}")
            continue  # Don't process sourced file contents as commands

        # Process all tokens
        for token in tokens:
            deps.update(process_token(token, cwd))

        # Check for executables
        potential_cmd = tokens[0]
        if "/" not in potential_cmd and re.match(r"^\w+$", potential_cmd):
            cmd_path = find_executable(potential_cmd)
            if cmd_path:
                deps.add(cmd_path)
                logger.debug(f"Added executable dependency: {cmd_path}")

    logger.info(f"Total dependencies found: {len(deps)}")
    return deps


def process_token(token: str, cwd: str) -> Set[str]:
    """Process a single token and return any dependencies found."""
    deps = set()
    # Expand environment variables
    expanded_token = os.path.expandvars(token)

    # Check for absolute file paths
    if expanded_token.startswith("/"):
        if os.path.exists(expanded_token):
            deps.add(expanded_token)
            logger.debug(f"Added absolute path dependency: {expanded_token}")

    # Check for relative paths and potential filenames
    elif "/" in expanded_token or "." in expanded_token:
        potential_file = os.path.join(cwd, expanded_token)
        if os.path.exists(potential_file):
            abs_path = os.path.abspath(potential_file)
            deps.add(abs_path)
            logger.debug(f"Added relative path dependency: {abs_path}")

    # Check for potential filenames without extension
    # Only consider tokens after specific commands or assignments
    elif (
        token not in tools_standard
        and not token.startswith("-")
        and any(
            prev_token in ["source", ".", "=", "+=", ":="]
            for prev_token in ("",)  # Add previous token logic here
        )
    ):
        potential_file = os.path.join(cwd, expanded_token)
        if os.path.exists(potential_file):
            abs_path = os.path.abspath(potential_file)
            deps.add(abs_path)
            logger.debug(f"Added potential file dependency: {abs_path}")

    return deps


def find_executable(cmd: str) -> Optional[str]:
    """Find the full path of an executable."""
    for path in os.environ.get("PATH", "").split(os.pathsep):
        cmd_path = os.path.join(path, cmd)
        if os.path.isfile(cmd_path) and os.access(cmd_path, os.X_OK):
            logger.debug(f"Executable found: {cmd_path}")
            return cmd_path
    logger.debug(f"Executable not found for command: {cmd}")
    return None


@arg("files", nargs="*", help="shell script files to analyze")
def sh_deps(
    *files: str,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Analyze shell scripts and output their dependencies.
    """
    get, put = main.io(istream, ostream)

    if not files:
        content = istream.read()
        deps = parse_script(content)
    else:
        deps = set()
        for file in files:
            try:
                with open(file, "r") as f:
                    content = f.read()
                deps.update(parse_script(content))
            except (IOError, OSError) as e:
                logger.error(f"Failed to read file {file}: {e}")

    for dep in sorted(deps):
        put(dep)


if __name__ == "__main__":
    main.run(sh_deps)
