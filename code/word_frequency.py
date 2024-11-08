#!/usr/bin/env python3-allemande

import sys
import collections


"""
word_frequency.py - A script to count word frequencies in input text.

This script can be used as a module:
    from word_frequency import word_count
"""


def word_count(text):
    """
    Counts the frequency of each word in the given text.

    Args:
        text (str): The input text to be processed.

    Returns:
        dict: A dictionary where keys are words and values are their corresponding frequencies.
    """
    words = text.split()
    return collections.Counter(words)


def main():
    """
    word_frequency.py - A script to count word frequencies in input text.

    This script reads text from stdin and prints word frequencies to stdout.

    Usage:
        cat input.txt | python3 word_frequency.py
    """
    input_text = sys.stdin.read()
    word_freq = word_count(input_text)
    for word, count in word_freq.items():
        print(f"{word}: {count}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e, file=sys.stderr)
