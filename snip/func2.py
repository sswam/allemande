#!/usr/bin/env python3-allemande


"""
func.py - A script to extract selected functions or methods from a Python source code file,
given a list of function names or class.method names.

Usage:
    python func.py <source_file> <func1> [<func2> ...]
"""

import sys
import re

def build_function_pattern():
    """Build the regex pattern for matching function definitions."""
    decorator = r'(?:@\w+(?:\(.*?\))?\s*\n)*'
    async_prefix = r'(?:async\s+)?'
    func_def = r'def\s+(\w+)'
    params = r'(?:\s*\((?:[^()]*|\([^()]*\))*\))'
    return_type = r'(?:\s*->.*?)?'
    colon_and_comment = r'\s*:(?:\s*#.*)?'
    function_body = r'(?:\n(?:[ \t].*(?:\n|$))*)'

    pattern = rf'{decorator}\s*{async_prefix}{func_def}{params}{return_type}{colon_and_comment}{function_body}'
    return pattern

def extract_functions(source_file, func_names):
    """
    Extract specified functions or methods from the given source file.
    """
    with open(source_file, 'r') as file:
        content = file.read()

    extracted_funcs = []
    pattern = build_function_pattern()

    for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
        func_def, func_name = match.group(0), match.group(1)
        if func_name in func_names or any(f"{class_name}.{func_name}" in func_names for class_name in func_names):
            extracted_funcs.append(func_def.strip())

    return extracted_funcs

def print_functions(functions):
    """
    Print the extracted functions with a blank line between each.
    """
    for func in functions:
        print(func)
        print()  # Add a blank line between functions

def main():
    if len(sys.argv) < 3:
        print("Usage: python func.py <source_file> <func1> [<func2> ...]")
        sys.exit(1)

    source_file = sys.argv[1]
    func_names = sys.argv[2:]

    extracted_funcs = extract_functions(source_file, func_names)
    print_functions(extracted_funcs)

if __name__ == "__main__":
    main()
