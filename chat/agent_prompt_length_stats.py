#!/usr/bin/env python3-allemande

"""
Calculate statistics for agent prompt lengths from YAML files.
"""

import os
import sys
from pathlib import Path

from ally import main, logs, yaml  # type: ignore

logger = logs.get_logger()


def get_agent_dirs() -> list[Path]:
    """Get the list of directories containing agent YAML files."""
    base_dirs = [
        os.environ.get("ALLEMANDE_AGENTS", ""),
        os.path.join(os.environ.get("ALLEMANDE_ROOMS", ""), "agents"),
        os.path.join(os.environ.get("ALLEMANDE_ROOMS", ""), "nsfw/agents"),
    ]
    return [Path(d) for d in base_dirs if d and Path(d).exists()]


def get_agent_files(dirs: list[Path]) -> list[Path]:
    """Find all .yml files in the given directories and their subdirectories."""
    return [f for d in dirs for f in d.rglob("*.yml")]


def get_prompts(yaml_file: Path) -> list[str]:
    """Extract system_top and system_bottom prompts from YAML file."""
    try:
        with yaml_file.open() as f:
            data = yaml.safe_load(f)
            prompts = []
            for key in ["system_top", "system_bottom"]:
                if data.get(key):
                    prompt = str(data[key]).strip()
                    if prompt and prompt != "null":
                        prompts.append(prompt)
            return prompts
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error processing %s: %s", yaml_file, e)
        return []


def count_stats(text: str) -> tuple[int, int, int]:
    """Count lines, words, and characters in text."""
    lines = [line for line in text.splitlines() if line.strip()]
    words = text.split()
    chars = len(text)
    return len(lines), len(words), chars


def process_files(istream=sys.stdin, ostream=sys.stdout) -> None:
    """Process agent YAML files and output prompt length statistics."""
    dirs = get_agent_dirs()
    files = get_agent_files(dirs)

    for file in files:
        prompts = get_prompts(file)
        if prompts:
            combined_text = "\n".join(prompts)
            lines, words, chars = count_stats(combined_text)
            print(lines, words, chars, file, sep="\t", file=ostream)


if __name__ == "__main__":
    main.go(process_files)
