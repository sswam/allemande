#!/usr/bin/env python3

"""
func.py - A script to extract selected functions or methods from a Python source code file,
given a list of function names or class.method names.

Usage:
    python func.py [-b] <source_file> <func1> [<func2> ...]

Options:
    -b    Use Black formatting (optional, off by default)
"""

import sys
import ast
import black

def extract_functions(source_file, func_names, use_black=False):
    """
    Extract specified functions or methods from the given source file.
    """
    with open(source_file, "r") as file:
        source_lines = file.readlines()
        source = "".join(source_lines)

    tree = ast.parse(source)
    extracted_funcs = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in func_names:
                extracted_funcs.append((node, source_lines))
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if f"{node.name}.{item.name}" in func_names:
                        extracted_funcs.append((item, source_lines))

    return extracted_funcs

def print_functions(functions, use_black=False):
    """
    Print the extracted functions with a blank line between each, optionally formatted using black.
    """
    mode = black.Mode() if use_black else None
    for func, source_lines in functions:
        original_source = "".join(source_lines[func.lineno-1:func.end_lineno])
        if use_black:
            try:
                formatted_source = black.format_str(original_source, mode=mode)
                print(formatted_source)
            except black.InvalidInput:
                print(original_source)  # Fallback to unformatted source if black fails
        else:
            print(original_source)
        print()  # Add a blank line between functions

def main():
    if len(sys.argv) < 3:
        print("Usage: python func.py [-b] <source_file> <func1> [<func2> ...]")
        sys.exit(1)

    use_black = False
    if sys.argv[1] == "-b":
        use_black = True
        sys.argv.pop(1)

    source_file = sys.argv[1]
    func_names = sys.argv[2:]

    extracted_funcs = extract_functions(source_file, func_names)
    print_functions(extracted_funcs, use_black)

if __name__ == "__main__":
    main()
