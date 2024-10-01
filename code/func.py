#!/usr/bin/env python3

"""
A script to extract and analyze functions, methods, and classes from source code files.
"""

import os
import sys
import ast
import logging
from typing import TextIO, Callable
import subprocess
import json

from argh import arg
import black

from ally import main
from reformat import reformat

__version__ = "0.1.5"

logger = main.get_logger()


def run(cmd, source):
    return subprocess.run(cmd, input=source.encode(), capture_output=True).stdout.decode()


def parse_source(source: str, language: str):
    if language == "py":
        tree = ast.parse(source)
    elif language == "sh":
        # Use "shfmt" to parse Bash scripts
        text = run(["shfmt", "-tojson"], source)
        tree = json.loads(text)
    elif language == "pl":
        # Use "perl -MO=Deparse" to parse Perl scripts
        text = run(["perl", "-MO=Deparse"], source)
        tree = text.split("\n")  # TODO
    elif language == "c":
        # Use "clang -Xclang -tree-dump" to parse C code
        text = run(["clang", "-Xclang", "-tree-dump", "-fsyntax-only", "-"], source)
        tree = text.split("\n")  # TODO
    else:
        raise ValueError(f"Unsupported language: {language}")
    return tree


def extract_items(tree, language: str):
    items = []
    if language == 'py':
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                items.append(node)
    # TODO Add parsing logic for other languages here
    return items


def format_item(item, types: bool, params: bool, decorators: bool, docstring: bool, language: str):
    if language == "py":
        name = item.name
        if types:
            name = f"{'class' if isinstance(item, ast.ClassDef) else 'def'} {name}"
        if params:
            name += f"({ast.unparse(item.args)})"
        if decorators:
            name = "\n".join([f"@{ast.unparse(d)}" for d in item.decorator_list] + [name])
        if docstring and ast.get_docstring(item):
            name += f"\n    \"\"\"{ast.get_docstring(item)}\"\"\""
    # Add formatting logic for other languages here
    return name


@arg("source_file", help="Path to the source file")
@arg("func_names", nargs="*", help="Names of functions, methods, or classes to extract")
@arg("-f", "--reformat", help="Reformat code", action="store_true", dest="reformat")
@arg("-a", "--all", help="Process all functions, methods, and classes", action="store_true", dest="process_all")
@arg("-A", "--all-info", help="Show all info except code", action="store_true", dest="show_all_info")
@arg("-n", "--names", help="Show only names", action="store_true", dest="show_names")
@arg("-t", "--types", help="Show types (def vs class, etc)", action="store_true", dest="show_types")
@arg("-p", "--params", help="Include full formal parameters", action="store_true", dest="show_params")
@arg("-d", "--decorators", help="Include decorators", action="store_true", dest="show_decorators")
@arg("-s", "--docstrings", help="Include docstrings", action="store_true", dest="show_docstrings")
@arg("-l", "--list", help="Alias for -a -n (list all names)", action="store_true", dest="list_mode")
@arg("--language", help="Language of the source file")
def process_source(
    source_file: str,
    func_names: list[str],
    reformat: bool = False,
    process_all: bool = False,
    show_all_info: bool = False,
    show_names: bool = False,
    show_types: bool = False,
    show_params: bool = False,
    show_decorators: bool = False,
    show_docstrings: bool = False,
    list_mode: bool = False,
    language: str = None,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Process and analyze source code file.
    """
    get, put = main.io(istream, ostream)

    # What are we gonna show?
    show_code = True
    if list_mode:
        process_all = True
        show_names = True
    if show_all_info:
        show_names = show_types = show_params = show_decorators = show_docstrings = True
    if show_names or show_types or show_params or show_decorators or show_docstrings:
        show_code = False

    # Where's the source code?
    if source_file == "-":
        source = get(all=True)
    else:
        with open(source_file) as f:
            source = f.read()

    # What language are we dealing with?
    if not language:
        language = os.path.splitext(source_file)[1][1:]
        if language not in ["py", "sh", "pl", "c"]:
            language = "py"

    tree = parse_source(source, language)
    items = extract_items(tree, language)

    if process_all:
        func_names = [item.name for item in items]

    for item in items:
        if item.name in func_names or f"{item.__class__.__name__}.{item.name}" in func_names:
            if show_code:
                source_code = ast.unparse(item) if language == "py" else source[item.start:item.end]

                # Reformatting is out of scope for this script, we should move it to a separate script.
                if reformat:
                    source_code = reformat(source_code, language)
                put(source_code)
            else:
                put(format_item(item, show_types, show_params, show_decorators, show_docstrings, language))
            put()

if __name__ == "__main__":
    main.run(process_source)
