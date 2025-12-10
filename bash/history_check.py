#!/usr/bin/env python3-allemande

"""
Analyze recent shell history and generate an AI summary of activities.
"""

import logging
from pathlib import Path
from typing import TextIO

from ally import main  # type: ignore
from ally.quote import quote_lines  # type: ignore
import llm  # type: ignore

__version__ = "0.1.2"

logger = logging.getLogger(__name__)

HISTORY_OVERSAMPLE = 4

exclude = quote_lines("""
    pwd
    fg
    ll
    ls
    jobs
    st
    ww
    dfh
    df
    re
    cd
    vi
    monitor
    spool-cleanup
    """)


def read_history_lines(count: int) -> list[str]:
    """Read the last n lines from .bash_history."""
    history_file = Path.home() / ".bash_history"
    lines = history_file.read_text().splitlines()
    return lines[-count:] if count > 0 else lines


def clean_history_line(line: str) -> str:
    """Remove timestamps and leading numbers from a history line."""
    line = line.strip()

    # Remove bash history timestamp format like #1234567890
    if line.startswith("#") and line[1:].split()[0].isdigit():
        return ""

    # Remove leading numbers and whitespace
    while line and (line[0].isdigit() or line[0].isspace()):
        line = line[1:]

    return line.strip()


def deduplicate_ordered(commands: list[str]) -> list[str]:
    """Remove duplicates while preserving order."""
    seen = set()
    result = []
    for cmd in commands:
        if cmd and cmd not in seen:
            seen.add(cmd)
            result.append(cmd)
    return result


def remove_prefixes(commands: list[str]) -> list[str]:
    """Remove commands that are prefixes of other commands."""
    # For each command, check if any other command starts with it plus a space
    result = []
    for i, cmd in enumerate(commands):
        is_prefix = False
        for j, other in enumerate(commands):
            if i != j and other.startswith(cmd + " "):
                is_prefix = True
                break
        if not is_prefix:
            result.append(cmd)
    return result


def remove_excluded(commands: list[str]) -> list[str]:
    """Remove commands that match excluded patterns (whole line match)."""
    excluded_set = set(exclude)
    return [cmd for cmd in commands if cmd not in excluded_set]


def history_check(
    ostream: TextIO,
    count: int = 50,
    model: str | None = None,
    prompt: str = "",
    raw_count: bool = False,
) -> None:
    """Analyze shell history and generate AI summary of activities."""
    sample_count = count if raw_count else count * HISTORY_OVERSAMPLE

    logger.info(f"reading last {sample_count} history lines")
    lines = read_history_lines(sample_count)

    # Clean and filter
    commands = [clean_history_line(line) for line in lines]
    commands = [cmd for cmd in commands if cmd]

    logger.info(f"removing excluded commands from {len(commands)} commands")
    commands = remove_excluded(commands)

    logger.info(f"deduplicating {len(commands)} commands")
    commands = deduplicate_ordered(commands)

    logger.info(f"removing prefix commands from {len(commands)} commands")
    commands = remove_prefixes(commands)

    # Take the most recent count after filtering
    commands = commands[-count:]

    logger.info(f"processing {len(commands)} commands with AI")

    # Build the command history text
    history_text = "\n".join(commands)

    # Create prompt for AI
    base_prompt = f"""## Based on the following shell command history, provide a summary of what the user has been working on.

- Focus on the main activities and goals. Give a simple, clear, very concise markdown list in style similar to this prompt, followed by a single-line overview or guess at the high-level task/s or goals here.
- Unless contradicted below, please default to a brief high-level dot point summary, structured, not necessarily chronological.
- don't include trivial stuff like use of standard toolkit, or mention use of this history-check tool itself.

Command history:
{history_text}

{prompt}"""

    # Process with AI
    response = llm.query(base_prompt, model=model or "")
    ostream.write(f"{response.strip()}\n")


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("count", nargs="?", help="number of history lines to analyze")
    arg("-m", "--model", help="specify which AI model e.g. claude, emmy, clia, dav")
    arg("-p", "--prompt", help="extra guidance/prompting to add to the base prompt")
    arg("-r", "--raw-count", help="sample exactly count lines instead of oversampling and filtering")


if __name__ == "__main__":
    main.go(history_check, setup_args)
