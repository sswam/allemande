#!/usr/bin/env python3-allemande

"""
A tool to find and replace text in files while preserving case sensitivity.
"""

import sys
import re
from typing import TextIO, List
from pathlib import Path

from argh import arg
import chardet

from ally import main

__version__ = "1.0.0"

logger = main.get_logger()


def detect_encoding(file_path: Path) -> str:
    """Detect the encoding of a file."""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    return chardet.detect(raw_data)['encoding']


def preserve_case(original: str, replacement: str) -> str:
    """Preserve the case of the original text in the replacement."""
    if original.islower():
        return replacement.lower()
    if original.isupper():
        return replacement.upper()
    if original.istitle():
        return replacement.capitalize()
    return replacement


def smart_replace(text: str, find: str, replace: str) -> str:
    """Replace text while preserving case sensitivity."""
    def repl(match):
        return preserve_case(match.group(0), replace)

    pattern = re.compile(re.escape(find), re.IGNORECASE)
    return pattern.sub(repl, text)


@arg("find", help="text to find")
@arg("replace", help="text to replace with")
@arg("files", nargs="*", help="files to process")
def replace_text(
    input: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    find: str = "",
    replace: str = "",
    files: List[str] = [],
) -> None:
    """
    Find and replace text in files while preserving case sensitivity.
    If no files are specified, it processes stdin and outputs to stdout.
    """
    get, put = main.io(input, output)

    if not files:
        content = get()
        modified_content = smart_replace(content, find, replace)
        put(modified_content)
    else:
        for file_path in files:
            path = Path(file_path)
            if not path.is_file():
                logger.warning(f"Skipping {file_path}: Not a file")
                continue

            encoding = detect_encoding(path)
            with path.open('r', encoding=encoding) as file:
                content = file.read()

            modified_content = smart_replace(content, find, replace)

            if content != modified_content:
                with path.open('w', encoding=encoding) as file:
                    file.write(modified_content)
                logger.info(f"Updated {file_path}")
            else:
                logger.info(f"No changes in {file_path}")


if __name__ == "__main__":
    main.run(replace_text)

# This tool can be particularly useful for batch editing of text files, code refactoring, or any scenario where you need to replace text while maintaining the original case structure.

# Certainly! I'll create a `useful.py` script in a similar style to `hello.py`, providing an unusual but useful Python tool. Here's the script:

# This script, `useful.py`, is a tool that finds and replaces text in files while preserving case sensitivity. Here's how to use it:
#
# 1. To replace text in files:

# python useful.py "old text" "new text" file1.txt file2.txt

# 2. To process stdin and output to stdout:

# echo "Hello World" | python useful.py "world" "Universe"

# 3. To see help and options:

# python useful.py --help

# This tool is unusual and useful because:
#
# 1. It preserves case sensitivity: If the original text is "World", "WORLD", or "world", the replacement will match that case.
# 2. It can handle multiple files in one invocation.
# 3. It automatically detects file encoding, making it work with various text encodings.
# 4. It can be used both as a command-line tool and as a module in other Python scripts.
#
# To use it as a module in another Python script:

# from useful import replace_text
#
# replace_text(find="old", replace="new", files=["example.txt"])
