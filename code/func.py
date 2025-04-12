#!/usr/bin/env python3-allemande

"""Extract, list and manipulate code blocks based on indentation structure."""

import os
import sys
import re
from typing import List, Optional
from ally import main, logs

logger = logs.get_logger()


def split_code_into_sections(text: str) -> List[str]:
    """
    Split source code text into sections based on double blank line boundaries,
    where the following line is not indented.
    """
    return re.split(
        rf"""
        (?<=\n)     # preceded by a newline
        \s*?\n+     # blank line
        (?!^[ \t])  # not followed by an indented line
        """,
        text,
        flags=re.VERBOSE | re.MULTILINE | re.DOTALL,
    )


def split_signature_body(block: str) -> tuple[str, str]:
    """Split a block into signature and body at last unindented non-label line."""
    # If no indented lines, return the whole block as signature
    if not re.search(r"^\s", block, re.MULTILINE):
        return block, ""
    pattern = r'''
        (                             # Match the signature
            .*
            ^(?!\w+:)                 # Not a goto label
            \S.*?\n                   # Non-indented line
            (?:^\s+""".*?"""\s*?\n)?  # optional indented docstring
        )
        (                             # Match the body
            .+                        # Non-empty body
        )
    '''
    m = re.match(pattern, block, re.MULTILINE | re.DOTALL | re.VERBOSE)
    if m:
        return m.group(1), m.group(2)
    return block, ""


def matches_block(signature: str, pattern: str) -> bool:
    """Check if signature matches a name or class.method pattern."""
    if "." in pattern:
        class_name, method_name = pattern.split(".", 1)
        return re.search(rf"\bclass\s+{class_name}\b", signature) and re.search(rf"\b{method_name}\b", signature)
    return bool(re.search(rf"\b{pattern}\b", signature))


def dedent(body: str) -> tuple[str, str]:
    """
    Remove common indentation from the body of a block.
    Return the new body and the indentation level.
    Skip comment lines when calculating minimum indentation.
    Only dedent lines that start with the common indent.
    """
    lines = body.splitlines()

    # Get non-empty, non-comment lines for indent calculation
    content_lines = [line for line in lines if not re.match(r"^\s*($|#|//|/\*)", line)]

    # Get the common indent text
    indent = re.match(r"^\s*", os.path.commonprefix(content_lines)).group()

    if not indent:
        return body, ""

    # Remove the common indent
    indent_length = len(indent)
    lines = [line[indent_length:] if line.startswith(indent) else line for line in lines]

    new_body = "\n".join(lines) + "\n"
    return new_body, indent


def list_blocks(text: str, indent: str = "") -> None:
    """Display all blocks, recursively handling classes."""
    blocks = split_code_into_sections(text)

    for block in blocks:
        signature, body = split_signature_body(block)
        if indent:
            signature = re.sub(r"^", indent, signature, flags=re.MULTILINE)
        # print(f"sig: [{signature}]")
        # print(f"body: [{body}]")
        print(signature.rstrip())

        # If this is a class, process its body
        if body and re.search(r"\bclass\b", signature):
            body2, indent2 = dedent(body)
            list_blocks(body2, indent + indent2)

        print()  # Blank line for separation


def extract_blocks(text: str, names: List[str], indent: str = "") -> List[str]:
    """Extract blocks matching given names, including nested class methods."""
    blocks = split_code_into_sections(text)
    result = []

    for block in blocks:
        signature, body = split_signature_body(block)

        # Check if this block matches any requested name
        for name in names:
            if matches_block(signature, name):
                result.append(block)
                break

        # If this is a class, check its body too
        if re.search(r"^\s*class\s+", signature, re.MULTILINE) and body:
            nested = extract_blocks(body, names, indent + "    ")
            result.extend(nested)

    return result


def process_file(
    source_file: str,
    names: List[str] = None,
    list_only: bool = False,
    extract: bool = False,
):
    """Process source file according to arguments."""
    try:
        with open(source_file) as f:
            text = f.read()
    except IOError as e:
        logger.error(f"Failed to read {source_file}: {e}")
        return

    if list_only:
        list_blocks(text)
        return

    if extract:
        blocks = extract_blocks(text, names)
        print("".join(blocks), end="")


def setup_args(arg):
    """Set up command-line arguments."""
    arg("source_file", help="Source code file to process")
    arg("names", nargs="*", help="Names of blocks to extract")
    arg(
        "-l",
        "--list",
        action="store_true",
        help="List all block signatures",
        dest="list_only",
    )
    arg("-x", "--extract", action="store_true", help="Extract named blocks")


if __name__ == "__main__":
    main.go(process_file, setup_args)
