#!/usr/bin/env python3

""" critiques files """

import sys
import llm

def critique(filename):
    prompt = "Please provide a *very* short critique."
    with open(filename, 'r') as istream:
        response = llm.process(prompt, istream=istream)
    print(f"## {filename}", end="\n\n")
    print(response, end="\n\n")

if __name__ == "__main__":
    for filename in sys.argv[1:]:
        critique(filename)
