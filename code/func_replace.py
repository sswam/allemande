#!/usr/bin/env python3

"""
A script to replace functions, methods, and classes in a Python code file.
"""

import sys
import ast
from typing import Dict, List, Tuple

from ally import main, filer, logs

__version__ = "0.1.0"

logger = logs.get_logger()


def parse_code(code: str) -> Tuple[ast.Module, List[str]]:
    """Parse the code and return the AST and lines."""
    tree = ast.parse(code)
    lines = code.split('\n')
    return tree, lines


def extract_items(tree: ast.Module) -> Dict[str, ast.AST]:
    """Extract functions, methods, and classes from the AST."""
    items = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            items[node.name] = node
    return items


def replace_items(original_lines: List[str], original_items: Dict[str, ast.AST],
                new_items: Dict[str, str]) -> Tuple[List[str], List[str]]:
    """Replace items in the original code with new items."""
    replaced_lines = original_lines.copy()
    used_items = []

    for name, node in sorted(original_items.items(), key=lambda x: x[1].lineno, reverse=True):
        if name in new_items:
            start = node.lineno - 1
            end = node.end_lineno
            replaced_lines[start:end] = new_items[name].split('\n')
            used_items.append(name)

    return replaced_lines, used_items


def add_new_items(lines: List[str], new_items: Dict[str, str], used_items: List[str]) -> List[str]:
    """Add new items that weren't used for replacement."""
    main_check_index = next((i for i, line in enumerate(lines) if line.strip().startswith("if __name__ == '__main__'")), len(lines))

    for name, code in new_items.items():
        if name not in used_items:
            lines.insert(main_check_index, '\n' + code + '\n')
            main_check_index += len(code.split('\n')) + 1
            logger.info(f"Added new item: {name}")

    return lines


def process_file(filename: str, new_items: Dict[str, str], add_option: bool) -> None:
    """Process the file, replacing or adding items as needed."""
    with open(filename, 'r') as f:
        original_code = f.read()

    original_tree, original_lines = parse_code(original_code)
    original_items = extract_items(original_tree)

    replaced_lines, used_items = replace_items(original_lines, original_items, new_items)

    if add_option:
        replaced_lines = add_new_items(replaced_lines, new_items, used_items)
    else:
        unused_items = set(new_items.keys()) - set(used_items)
        if unused_items:
            logger.warning(f"The following items were not used: {', '.join(unused_items)}")

    filer.backup(filename)
    with open(filename, 'w') as f:
        f.write('\n'.join(replaced_lines))

    logger.info(f"Updated file: {filename}")


def func_replace(filename: str, add: bool = False) -> None:
    # Read all of stdin into a string and a list of lines
    source = sys.stdin.read()
    lines = source.splitlines()

    # Parse the source code
    tree = ast.parse(source)

    new_items = {}

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            name = node.name
            if isinstance(node.parent, ast.ClassDef):
                name = f"{node.parent.name}.{name}"
            start_line = node.lineno - 1
            end_line = node.end_lineno
            new_items[name] = '\n'.join(lines[start_line:end_line])

        def visit_ClassDef(self, node):
            name = node.name
            start_line = node.lineno - 1
            end_line = node.end_lineno
            new_items[name] = '\n'.join(lines[start_line:end_line])
            self.generic_visit(node)

    # Add parent information to nodes
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node

    # Visit the AST
    visitor = Visitor()
    visitor.visit(tree)

    process_file(filename, new_items, add)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("filename", help="The Python file to modify")
    arg("--add", action="store_true", help="Add new items instead of warning about unused ones")


if __name__ == "__main__":
    main.go(func_replace, setup_args)

