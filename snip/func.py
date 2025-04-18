#!/usr/bin/env python3-allemande

"""
A script to extract and analyze functions, methods, and classes from source code files.
"""

import os
import ast
from typing import TextIO
import subprocess
import json
import re

import black

from ally import main, logs, geput  # type: ignore
from reformat import reformat as reformat_code

__version__ = "0.1.9"

logger = logs.get_logger()


def run(cmd, source):
    return subprocess.run(cmd, input=source.encode(), capture_output=True, check=True).stdout.decode()


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
        tree = text.split("\n")  # TODO: Implement proper parsing for Perl
    elif language == "c":
        # Use "clang -Xclang -tree-dump" to parse C code
        text = run(["clang", "-Xclang", "-tree-dump", "-fsyntax-only", "-"], source)
        tree = text.split("\n")  # TODO: Implement proper parsing for C
    else:
        raise ValueError(f"Unsupported language: {language}")
    return tree


def _handle_function_node(node, class_methods, items):
    """Process function/async function nodes."""
    if isinstance(getattr(node, "parent", None), ast.ClassDef):
        class_name = node.parent.name
        if class_name not in class_methods:
            class_methods[class_name] = []
        class_methods[class_name].append(node)
    else:
        items.append(node)


def _extract_python_items(tree):
    """Extract items specifically from Python AST."""
    items = []
    class_methods = {}

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _handle_function_node(node, class_methods, items)
        elif isinstance(node, ast.ClassDef):
            items.append(node)

    # Add class methods after their classes
    for methods in class_methods.values():
        items.extend(methods)

    return items


def extract_items(tree, language: str):
    """Extract functions, classes and methods from the AST."""
    if language == "py":
        return _extract_python_items(tree)
    return []


def format_item(item, types: bool, params: bool, decorators: bool, docstring: bool, language: str):
    """Format the item for display"""
    text = ""
    if language != "py":
        # TODO Add formatting logic for other languages
        return text + "\n"
    if isinstance(item, ast.FunctionDef):
        # Handle nested functions
        parent_func = item.parent if hasattr(item, "parent") and isinstance(item.parent, ast.FunctionDef) else None
        parent_class = item.parent if hasattr(item, "parent") and isinstance(item.parent, ast.ClassDef) else None

        if parent_func:
            text = f"{parent_func.name}.{item.name}"
        elif parent_class:
            text = f"{parent_class.name}.{item.name}"
        else:
            text = item.name
    else:
        text = item.name
    is_class = isinstance(item, ast.ClassDef)
    if types:
        text = f"{'class' if is_class else 'def'} {text}"
    if params and not is_class:
        text += f"({ast.unparse(item.args)})"
    if decorators:
        text = "\n".join([f"@{ast.unparse(d)}" for d in item.decorator_list] + [text])
    if docstring:
        text += ":"
        if ast.get_docstring(item):
            docstring = ast.get_docstring(item)
            multiline = "\n" in docstring
            if multiline:
                indented = re.sub(r"(?m)^", "    ", docstring)
                text += f'\n    """\n{indented}\n    """'
            else:
                text += f'\n    """{docstring}"""'


def func(
    istream: TextIO,
    put: geput.Put,
    source_file: str,
    *func_names: str,
    reformat: bool = False,
    process_all: bool = False,
    show_info: bool = False,
    show_names: bool = False,
    show_types: bool = False,
    show_params: bool = False,
    show_decorators: bool = False,
    show_docstrings: bool = False,
    list_mode: bool = False,
    language: str | None = None,
    show_all_info: bool = False,
) -> None:
    """
    Process and analyze source code file.
    """
    # What are we gonna show?
    show_code = True
    if list_mode:
        process_all = True
        show_names = True
    if show_all_info:
        process_all = True
        show_info = True
    if show_info:
        show_names = show_types = show_params = show_decorators = show_docstrings = True
    if show_names or show_types or show_params or show_decorators or show_docstrings:
        show_code = False

    gap = show_code or show_decorators or show_docstrings

    # Where's the source code?
    if source_file == "-":
        source = istream.read()
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

    source_lines = [""] + source.split("\n")

    for item in items:
        if item.name not in func_names and f"{item.__class__.__name__}.{item.name}" not in func_names:
            continue
        if show_code:
            # source_code = ast.unparse(item) if language == "py" else source[item.start:item.end]
            source_code = "\n".join(source_lines[item.lineno : item.end_lineno + 1] + [""])

            # Reformatting should be out of scope for this script, we should move it to a separate script.
            if reformat:
                source_code = reformat_code(source_code, language)

            put(source_code)
        else:
            put(format_item(item, show_types, show_params, show_decorators, show_docstrings, language))
        if gap:
            put("\n")


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("source_file", help="Path to the source file")
    arg("func_names", nargs="*", help="Names of functions, methods, or classes to extract")
    arg("-f", "--reformat", help="Reformat code", action="store_true")
    arg("-a", "--all", help="Process all functions, methods, and classes", action="store_true", dest="process_all")
    arg("-I", "--info", help="Show all info except code", action="store_true", dest="show_info")
    arg("-n", "--names", help="Show only names", action="store_true", dest="show_names")
    arg("-t", "--types", help="Show types (def vs class, etc)", action="store_true", dest="show_types")
    arg("-p", "--params", help="Include full formal parameters", action="store_true", dest="show_params")
    arg("-d", "--docstrings", help="Include docstrings", action="store_true", dest="show_docstrings")
    arg("-D", "--decorators", help="Include decorators", action="store_true", dest="show_decorators")
    arg("-l", "--list", help="Alias for -a -n (list all names)", action="store_true", dest="list_mode")
    arg("-A", "--all-info", help="Alias for -a -I (show all info)", action="store_true", dest="show_all_info")
    arg("--language", help="Language of the source file")


if __name__ == "__main__":
    main.go(func, setup_args)
