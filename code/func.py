#!/usr/bin/env python3-allemande

"""
A script to extract and analyze functions, methods, and classes from Python source code.
"""

import ast
from typing import TextIO
import re

from ally import main, logs  # type: ignore

__version__ = "0.1.13"

logger = logs.get_logger()


def _handle_function_node(node, class_methods, items):
    """Process function/async function nodes."""
    parent = getattr(node, "parent", None)
    if isinstance(parent, ast.ClassDef):
        class_name = parent.name
        if class_name not in class_methods:
            class_methods[class_name] = []
        class_methods[class_name].append(node)
    elif isinstance(parent, ast.FunctionDef):
        # For nested functions, add them with parent prefix
        items.append(node)
    else:
        items.append(node)


def extract_items(tree):
    """Extract items specifically from Python AST."""
    items = []
    class_methods = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    child.parent = node
            items.append(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Set parent for nested functions
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    child.parent = node
            _handle_function_node(node, class_methods, items)

    # Add properly formatted class methods
    final_items = []
    for item in items:
        final_items.append(item)
        if isinstance(item, ast.ClassDef) and item.name in class_methods:
            for method in class_methods[item.name]:
                final_items.append(method)

    return final_items


def format_item(item, types: bool = False, params: bool = False, decorators: bool = False, docstring: bool = False) -> str:
    """Format the item for display"""
    text = ""
    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
        # Handle nested functions by checking parent chain
        parent = getattr(item, "parent", None)
        if parent and isinstance(parent, ast.FunctionDef):
            text = f"{parent.name}.{item.name}"
        elif parent and isinstance(parent, ast.ClassDef):
            text = f"{parent.name}.{item.name}"
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
        doc = ast.get_docstring(item)
        if doc:
            if "\n" in doc:
                indented = "\n".join(f"    {line}" for line in doc.split("\n"))
                text += f'\n    """\n{indented}\n    """'
            else:
                text += f'\n    """{doc}"""'
    return text


def func(  # pylint: disable=too-many-arguments,too-many-locals
    istream: TextIO,
    ostream: TextIO,
    source_file: str,
    *func_names: str,
    process_all: bool = False,
    show_info: bool = False,
    show_names: bool = False,
    show_types: bool = False,
    show_params: bool = False,
    show_decorators: bool = False,
    show_docstrings: bool = False,
    list_mode: bool = False,
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
        with open(source_file, encoding="utf-8") as f:
            source = f.read()

    tree = ast.parse(source)
    items = extract_items(tree)

    if process_all:
        func_names = tuple(format_item(item) for item in items)

    source_lines = [""] + source.split("\n")

    for item in items:
        name = format_item(item)
        if name not in func_names:
            continue
        if show_code:
            source_code = "\n".join(source_lines[item.lineno : item.end_lineno + 1] + [""]) + "\n"

            ostream.write(source_code)
        else:
            ostream.write(format_item(item, show_types, show_params, show_decorators, show_docstrings) + "\n")
        if gap:
            ostream.write("\n")


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("source_file", help="Path to the source file")
    arg("func_names", nargs="*", help="Names of functions, methods, or classes to extract")
    arg("-a", "--all", help="Process all functions, methods, and classes", action="store_true", dest="process_all")
    arg("-I", "--info", help="Show all info except code", action="store_true", dest="show_info")
    arg("-n", "--names", help="Show only names", action="store_true", dest="show_names")
    arg("-t", "--types", help="Show types (def vs class, etc)", action="store_true", dest="show_types")
    arg("-p", "--params", help="Include full formal parameters", action="store_true", dest="show_params")
    arg("-d", "--docstrings", help="Include docstrings", action="store_true", dest="show_docstrings")
    arg("-D", "--decorators", help="Include decorators", action="store_true", dest="show_decorators")
    arg("-l", "--list", help="Alias for -a -n (list all names)", action="store_true", dest="list_mode")
    arg("-A", "--all-info", help="Alias for -a -I (show all info)", action="store_true", dest="show_all_info")


if __name__ == "__main__":
    main.go(func, setup_args)
