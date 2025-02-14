#!/usr/bin/env python3-allemande

"""
Validate matching pairs of braces, brackets, and parentheses in text.
"""

import sys

from ally import main, logs  # type: ignore

__version__ = "0.1.1"

logger = logs.get_logger()


def check_braces(text: str) -> str:
    """Check if braces in the given text are properly matched and nested."""
    stack: list[tuple[str, int]] = []
    pairs = {")": "(", "}": "{", "]": "["}

    for i, char in enumerate(text.splitlines(), start=1):
        for j, c in enumerate(char, start=1):
            if c in "({[":
                stack.append((c, i))
            elif c in ")}]":
                if not stack:
                    return f"Mismatch at line {i}, column {j}: {c}"
                last_open, line_num = stack.pop()
                if last_open != pairs[c]:
                    return f"Mismatch at line {i}, column {j}: {c}"

    if stack:
        char, line_num = stack[-1]
        return f"Unclosed brace at line {line_num}: {char}"

    return "Braces match correctly"


def check_braces_cli() -> None:
    """Check brace matching in code from stdin."""
    text = sys.stdin.read()
    result = check_braces(text)
    print(result)


def setup_args(arg) -> None:  # pylint: disable=unused-argument
    """Set up the command-line arguments."""


if __name__ == "__main__":
    main.go(check_braces_cli, setup_args)
