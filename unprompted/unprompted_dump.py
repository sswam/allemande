#!/usr/bin/env python

"""
Unprompted Dump

This module processes 'unprompted' input templates, transforming variable assignments
into a format that displays the values of those variables.

It reads from standard input and writes to standard output.
"""

import sys
import re

def process_input():
    """
    Process input lines, transforming [sets ...] markups into variable displays.

    This function reads lines from standard input, processes each line to
    identify and transform [sets ...] markups, and prints the result to
    standard output.

    For lines containing [sets ...]:
    - Extracts variable assignments
    - Transforms them into a format: name=[get name]
    - Multiple assignments are comma-separated

    Lines without [sets ...] are printed unchanged.

    Returns:
        None
    """
    for line in sys.stdin:
        line = line.strip()

        if m := re.search(r'\[sets (.*?)\]', line):
            assignments_s = m[1]
            assignments = re.findall(r'(\w+)=(".*?"|\S*)', assignments_s)

            first = True
            for name, value in assignments:
                sep = "" if first else ", "
                print(f"{sep}{name}=[get {name}]", end="")
                first = False
            print()
        else:
            print(line)

# Run the input processing function
process_input()
