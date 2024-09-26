#!/usr/bin/env python3

import sys
import argh


"""
reverse_lines.py - A Python script to reverse individual lines of input.

This script can be used as a module:
    from reverse_lines import reverse_lines
"""


def reverse_lines(lines):
    """
    Reverses each line in the given list of lines.

    Args:
        lines (list of str): List of input lines to be reversed.

    Returns:
        list of str: List of reversed lines.
    """
    return [line.rstrip("\n")[::-1]+"\n" for line in lines]


def main():
    """
    reverse_lines.py - A Python script to reverse individual lines of input.

    This script reads lines from stdin and writes the reversed lines to stdout.

    Usage:
        cat input.txt | python3 reverse_lines.py
    """
    input_lines = sys.stdin.readlines()
    output_lines = reverse_lines(input_lines)
    for line in output_lines:
        sys.stdout.write(line)


if __name__ == '__main__':
    try:
        argh.dispatch_command(main)
    except Exception as e:
        print(e, file=sys.stderr)
