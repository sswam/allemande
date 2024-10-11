#!/usr/bin/env python3

import sys
import argparse
from typing import Iterable, Union

def core_function(input_data: Iterable[str]) -> Iterable[str]:
    # Core logic here
    pass

def process_string(input_string: str) -> str:
    return '\n'.join(core_function(input_string.splitlines()))

def process_file(input_file: str, output_file: str = None):
    with open(input_file, 'r') as infile:
        result = core_function(infile)
        if output_file:
            with open(output_file, 'w') as outfile:
                for line in result:
                    outfile.write(line + '\n')
        else:
            for line in result:
                print(line)

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout)
    args = parser.parse_args()

    for line in core_function(args.input):
        args.output.write(line + '\n')

if __name__ == '__main__':
    cli()

# To create versatile Python functions that work as both library functions and CLI tools:
#
# 1. Design core logic to work with strings or iterable input/output.
# 2. Create wrapper functions for different input/output types (file, string, list, stream).
# 3. Implement a CLI wrapper using argparse or click.
# 4. Use typing for clear function signatures.
#
# Example structure:

# This structure allows for flexible usage as both a library and CLI tool.

