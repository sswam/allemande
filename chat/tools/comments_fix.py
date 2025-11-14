#!/usr/bin/env python3-allemande

"""
Fix and align inline comments in Python code.
"""

import re
from typing import TextIO

from ally import main  # type: ignore

__version__ = "0.1.0"


def fix_comment_spacing(line: str) -> str:
    """Replace irregular spacing before inline comments with a single tab."""
    # Match non-whitespace followed by whitespace then #
    # Don't match lines that start with whitespace and # (those are full-line comments)
    pattern = r'([^ \t])([ \t]+)(#)'

    # Only process if there's actual code before the comment
    if match := re.search(pattern, line):
        # Check if there's non-whitespace before the match (i.e., it's not a standalone comment)
        prefix = line[:match.start(1)]
        if prefix and not prefix.isspace():
            return re.sub(pattern, r'\1\t\3', line)

    return line


def align_comments(lines: list[str], tab_width: int = 4) -> list[str]:
    """Align inline comments to a consistent column using spaces."""
    # Find all lines with inline comments and their comment positions
    comment_lines = []
    for i, line in enumerate(lines):
        # Skip lines that are only comments (start with optional whitespace then #)
        if re.match(r'^\s*#', line):
            continue

        # Find inline comments (code followed by tab then #)
        if match := re.search(r'([^\t])\t#', line):
            # Calculate visual column position of the code before tab
            code_part = line[:match.end(1)]
            visual_col = len(code_part.expandtabs(tab_width))
            comment_lines.append((i, visual_col, match.end(1)))

    if not comment_lines:
        return lines

    # Find a good alignment column (round up to next multiple of 4, minimum 48)
    max_code_col = max(col for _, col, _ in comment_lines)
    align_col = max(48, ((max_code_col + 3) // 4 + 1) * 4)

    # Align comments
    result = lines.copy()
    for line_idx, visual_col, tab_pos in comment_lines:
        line = result[line_idx]
        code_part = line[:tab_pos]
        comment_part = line[tab_pos + 1:].lstrip('\t')  # Remove tab before #

        # Calculate spaces needed
        spaces_needed = align_col - visual_col
        if spaces_needed < 2:
            spaces_needed = 2  # Minimum 2 spaces before comment

        result[line_idx] = code_part + ' ' * spaces_needed + comment_part

    return result


def comments_fix(
    istream: TextIO,
    ostream: TextIO,
    tab_width: int = 4,
) -> None:
    """Fix and align inline comments in Python code."""
    lines = istream.readlines()

    # First pass: normalize spacing before comments to tabs
    lines = [fix_comment_spacing(line) for line in lines]

    # Second pass: align comments using spaces
    lines = align_comments(lines, tab_width)

    # Write output
    for line in lines:
        ostream.write(line)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-t", "--tab-width", type=int, help="tab width for calculating alignment (default: 4)")


if __name__ == "__main__":
    main.go(comments_fix, setup_args)

# <think>
# Let me understand what's needed:
#
# 1. Create `comments_fix.py` in the style of `hello_py.py`
# 2. It should fix inline comments that have irregular spacing before the `#`
# 3. The pattern s/\([^ ^I]\)[ ^I]*#/\1^I#/ suggests:
# - Find non-whitespace characters followed by spaces/tabs then `#`
# - Replace with the character, a tab, then `#`
# 4. Then align comments properly using spaces
#
# So the tool should:
# - Read Python code
# - Find lines with inline comments (code + comment on same line)
# - Normalize the spacing before the `#` to use a tab
# - Then align all inline comments to a common column using spaces
#
# Looking at the regex pattern more carefully:
# - `\([^ ^I]\)` = capture a non-space, non-tab character
# - `[ ^I]*` = match zero or more spaces or tabs
# - `#` = match the hash
# - Replace with `\1^I#` = the captured char, a tab, then hash
#
# Actually, I think the approach is:
# 1. First pass: replace irregular spacing before inline comments with a single tab
# 2. Second pass: align the comments to a consistent column
#
# Let me write this following the style guide - simple, clear, using stdio.
# </think>
