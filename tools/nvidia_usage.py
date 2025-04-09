#!/usr/bin/env python3-allemande

# -*- coding: utf-8 -*-

"""
Reports GPU memory usage per process in MiB, paired with the full command line.

Runs nvidia-smi, parses its output using regular expressions to find processes
utilizing GPU memory, retrieves their PIDs and memory usage, and then uses ps
to find the full command line for each PID. Outputs the results as TSV
(Tab-Separated Values) with memory usage (in MiB) first, followed by the command.
"""

import sys
import re
import logging
from typing import TextIO

# Third-party imports
import sh  # type: ignore

# Local imports
# Assuming 'ally' is a local library available in the execution environment
# If not, replace with appropriate standard library imports or adjust setup
try:
    from ally import main, logs  # type: ignore
except ImportError:
    print("Error: Missing 'ally' library.", file=sys.stderr)
    sys.exit(1)


__version__ = "0.1.0"

logger = logs.get_logger()

# Regex to capture PID and Memory from nvidia-smi process lines
# Example line format from nvidia-smi output:
# |    0   N/A  N/A           97643      G   /usr/lib/xorg/Xorg                      600MiB |
# Capture group 'pid': The process ID (e.g., 97643)
# Capture group 'mem': The GPU memory usage in MiB (e.g., 600)
PROC_LINE_RE = re.compile(
    r"^\s*\|\s*\d+\s+.*?\s+(?P<pid>\d+)\s+\S+\s+.*?\s+(?P<mem>\d+)\s*MiB\s*\|$"
)


def get_command_line(pid: int) -> str:
    """Fetches the full command line for a given PID using ps."""
    try:
        # Use ps to get the full command line, including arguments
        # -o command= : Output only the command column without a header
        # -p pid      : Specify the process ID
        # Using ww to prevent command line truncation
        cmd = sh.ps("ww", "-o", "command=", "-p", str(pid)).strip()
        # Replace embedded newlines (can happen with very long commands/args shown by ps)
        # with spaces for cleaner single-line TSV output.
        return cmd.replace("\n", " ")
    except sh.ErrorReturnCode_1:
        # ErrorReturnCode_1 typically means the process with PID does not exist
        # This happens if the process finished between nvidia-smi and ps calls.
        logger.warning(f"Process {pid} not found by ps (likely finished).")
        return f"<process {pid} finished>"
    except Exception as e:  # pylint: disable=broad-except
        # Catch other potential errors during ps execution
        logger.error(f"Error running ps for PID {pid}: {e}")
        return f"<error fetching command for {pid}>"


def nvidia_usage(istream: TextIO, ostream: TextIO) -> None:
    """
    Runs nvidia-smi, parses its output, and prints GPU memory usage (MiB)
    and command line for each process in TSV format.
    """
    # istream is unused in this script but is part of the standard function
    # signature expected by ally.main.go
    _ = istream

    try:
        # Run nvidia-smi without arguments to get the default text output
        smi_output = sh.nvidia_smi(_err_to_out=True) # Capture stderr too, just in case
        logger.debug("nvidia-smi command executed successfully.")
    except sh.CommandNotFound:
        logger.error("nvidia-smi command not found. Is NVIDIA driver installed and in PATH?")
        # Critical error, cannot proceed without nvidia-smi
        sys.exit(1) # Use exit code 1 for command not found
    except sh.ErrorReturnCode as e:
        # Handle potential errors from nvidia-smi itself
        logger.error(f"nvidia-smi command failed with exit code {e.exit_code}:")
        logger.error(f"Stdout:\n{e.stdout.decode(errors='replace')}")
        logger.error(f"Stderr:\n{e.stderr.decode(errors='replace')}")
        sys.exit(e.exit_code or 1) # Exit with the command's exit code
    except Exception as e: # pylint: disable=broad-except
        # Catch any other unexpected exceptions during command execution
        logger.error(f"Failed to run nvidia-smi due to an unexpected error: {e}")
        sys.exit(1)

    in_process_section = False
    found_process_header = False
    # Store results as (memory_mib, command_line_string) tuples
    results: list[tuple[int, str]] = []

    # Parse the output line by line
    lines = str(smi_output).splitlines()
    for i, line in enumerate(lines):
        stripped_line = line.strip()

        # Detect the start of the processes section table
        if stripped_line.startswith("| Processes:"):
            in_process_section = True
            continue # Move to the next line

        # Inside the process section, find the header line marker
        if in_process_section and not found_process_header:
            # Header looks like: |=====================...===|
            if stripped_line.startswith("|==="):
                found_process_header = True
                logger.debug("Found Processes section header line.")
            continue # Move to the next line after the header

        # Once we've found the header, look for process lines
        if found_process_header:
            # Check if we've reached the end of the process table section
            # Footer looks like: +---------------------...---+
            if stripped_line.startswith("+--"):
                logger.debug("Found end of Processes section.")
                break # Stop processing lines, we are past the process list

            # Try to match the line against the process regex
            match = PROC_LINE_RE.match(line)
            if match:
                pid = int(match.group("pid"))
                mem_mib = int(match.group("mem"))
                logger.debug(f"Matched process PID: {pid}, Memory: {mem_mib} MiB")
                # Get the command line for this PID immediately
                command_line = get_command_line(pid)
                results.append((mem_mib, command_line))
            # else: The line is within the process section but doesn't match the regex
            # (e.g., could be a blank line, or a line for MIG instances if enabled)
            # We simply ignore non-matching lines within the table body.

    if not results:
        logger.info("No active GPU processes found in nvidia-smi output.")
        return # Nothing more to do

    # Print the collected results in TSV format
    logger.debug(f"Printing results for {len(results)} processes.")
    try:
        for mem_mib, command_line in results:
            # Output format: MemoryUsageMiB<TAB>FullCommandLine
            print(f"{mem_mib}\t{command_line}", file=ostream)
            # Flush the output stream to ensure results are visible promptly
            ostream.flush()
    except BrokenPipeError:
        # This occurs if the script's output is piped to a command that exits early
        # (e.g., nvidia_usage.py | head). This is not an error for the script.
        logger.warning("Output pipe closed (BrokenPipeError). Exiting gracefully.")
        # Python might try to write traceback to stderr on exit when pipe is broken
        # Closing stderr manually might prevent some of these messages.
        try:
            sys.stderr.close()
        except OSError:
            pass # Ignore errors closing stderr (it might already be closed)
        sys.exit(0) # Exit with success code
    except Exception as e: # pylint: disable=broad-except
        logger.error(f"An unexpected error occurred while writing output: {e}")
        sys.exit(1)


def setup_args(parser):
    """Set up the command-line arguments (currently none needed)."""
    # No custom arguments are defined for this script yet.
    # parser object provided by ally.main.go can be used here if needed.
    pass


if __name__ == "__main__":
    # Use ally.main.go to handle setup (logging, IO streams) and run the main function
    main.go(nvidia_usage, setup_args=setup_args)
