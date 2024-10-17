#!/usr/bin/env python3

"""
This module automatically refactors Python code based on specified requirements.
It can apply Part 1 and Part 2 transforms or just Part 2 transforms as needed.
"""

import re
import ast
from typing import Any, List, Tuple, Dict
import astor  # type: ignore

from ally import main, logs, geput  # type: ignore

__version__ = "0.1.2"

logger = logs.get_logger()


def remove_argh_imports(code: str) -> str:
    """Remove imports related to argh."""
    lines = code.split('\n')
    return '\n'.join(line for line in lines if not re.match(r'^\s*(from argh import|import argh)', line))


def change_main_call(code: str, main_func_name: str) -> str:
    """Change the if __name__ == "__main__" code to use main.go()."""
    pattern = r'if\s+__name__\s*==\s*["\']__main__["\']\s*:\s*\n\s*main\.run\((.*?)\)'
    replacement = f'if __name__ == "__main__":\n    main.go({main_func_name}, setup_args)'
    return re.sub(pattern, replacement, code, flags=re.DOTALL)


def extract_arg_decorators(code: str) -> List[Tuple[List[Any], Dict[str, Any]]]:
    """Extract @arg decorators from the code."""
    tree = ast.parse(code)
    arg_decorators = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            new_decorator_list = []
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and getattr(decorator.func, 'id', '') == 'arg':
                    args = [astor.to_source(arg).strip() for arg in decorator.args]
                    kwargs = {kw.arg: astor.to_source(kw.value).strip() for kw in decorator.keywords}
                    arg_decorators.append((args, kwargs))
                else:
                    new_decorator_list.append(decorator)
            node.decorator_list = new_decorator_list  # Remove @arg decorators
    return arg_decorators


def create_setup_args_function(arg_decorators: List[Tuple[List[Any], Dict[str, Any]]]) -> str:
    """Create a setup_args function based on extracted @arg decorators."""
    setup_args_code = "def setup_args(arg):\n    \"\"\"Set up the command-line arguments.\"\"\"\n"
    for args, kwargs in arg_decorators:
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        all_args = args + ([kwargs_str] if kwargs_str else [])
        setup_args_code += f"    arg({', '.join(all_args)})\n"
    return setup_args_code


def update_main_function_signature(code: str, main_func_name: str) -> str:
    """Update the main function signature to include get and put parameters."""
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == main_func_name:
            # Check if 'get' and 'put' are already in the arguments
            existing_args = [arg.arg for arg in node.args.args]
            if 'get' not in existing_args:
                node.args.args.append(
                    ast.arg(arg='get', annotation=ast.Attribute(value=ast.Name(id='geput', ctx=ast.Load()), attr='Get', ctx=ast.Load()))
                )
            if 'put' not in existing_args:
                node.args.args.append(
                    ast.arg(arg='put', annotation=ast.Attribute(value=ast.Name(id='geput', ctx=ast.Load()), attr='Put', ctx=ast.Load()))
                )
            # Add 'print = geput.print(put)' at the beginning of the function if 'put' is used
            if 'put' in existing_args or any('put' in astor.to_source(n) for n in ast.walk(node)):
                assign_print = ast.parse("print = geput.print(put)").body[0]
                node.body.insert(0, assign_print)
            break
    return astor.to_source(tree)


def apply_part1_transforms(code: str) -> str:
    """Apply Part 1 transforms to the code."""
    code = remove_argh_imports(code)
    main_func_match = re.search(r'def\s+(\w+)\s*\(', code)
    main_func_name = main_func_match.group(1) if main_func_match else 'main'
    code = change_main_call(code, main_func_name)
    arg_decorators = extract_arg_decorators(code)
    setup_args_func = create_setup_args_function(arg_decorators)
    # Insert setup_args function before 'if __name__ == "__main__"'
    code = re.sub(r'^if\s+__name__\s*==\s*["\']__main__["\']', f'{setup_args_func}\n\nif __name__ == "__main__"', code, flags=re.MULTILINE)
    code = update_main_function_signature(code, main_func_name)
    return code


def update_io_interface(code: str) -> str:
    """Update the IO interface as specified in Part 2."""
    # Ensure 'geput' is imported from 'ally'
    if 'from ally import' in code and 'geput' not in code:
        code = re.sub(r'^(from ally import .*)', r'\1, geput', code, flags=re.MULTILINE)
    elif 'from ally import' not in code:
        code = 'from ally import geput\n' + code

    class FunctionSignatureModifier(ast.NodeTransformer):
        def __init__(self):
            self.modified_functions = []

        def visit_FunctionDef(self, node):
            # Check if 'get' and 'put' parameters exist and add annotations
            for arg in node.args.args:
                if arg.arg == 'get':
                    arg.annotation = ast.Attribute(value=ast.Name(id='geput', ctx=ast.Load()), attr='Get', ctx=ast.Load())
                elif arg.arg == 'put':
                    arg.annotation = ast.Attribute(value=ast.Name(id='geput', ctx=ast.Load()), attr='Put', ctx=ast.Load())
            # Add 'get' and 'put' parameters if they don't exist
            existing_args = [arg.arg for arg in node.args.args]
            if 'get' not in existing_args:
                node.args.args.append(
                    ast.arg(arg='get', annotation=ast.Attribute(value=ast.Name(id='geput', ctx=ast.Load()), attr='Get', ctx=ast.Load()))
                )
            if 'put' not in existing_args:
                node.args.args.append(
                    ast.arg(arg='put', annotation=ast.Attribute(value=ast.Name(id='geput', ctx=ast.Load()), attr='Put', ctx=ast.Load()))
                )
            self.generic_visit(node)
            self.modified_functions.append(node.name)
            return node

    def modify_function_signature(code):
        tree = ast.parse(code)
        transformer = FunctionSignatureModifier()
        modified_tree = transformer.visit(tree)
        return astor.to_source(modified_tree)

    code = modify_function_signature(code)

    # Replace 'put' calls with 'print'
    pattern_put = r'(\b)put\('
    code = re.sub(pattern_put, r'\1print(', code)

    # Add 'print = geput.print(put)' if 'put' is used
    if 'print = geput.print(put)' not in code and re.search(r'\bprint\(', code):
        code_lines = code.splitlines()
        for idx, line in enumerate(code_lines):
            if line.strip().startswith('def '):
                # Insert 'print = geput.print(put)' after the function definition
                code_lines.insert(idx + 1, '    print = geput.print(put)')
                code = '\n'.join(code_lines)
                break

    # Replace 'get(all=True)' with 'geput.whole(get)'
    code = re.sub(r'\bget\(all=True\)', 'geput.whole(get)', code)

    # Replace 'get()' with 'input()' and add 'input = geput.input(get)'
    if 'get()' in code:
        code = re.sub(r'\bget\(\)', 'input()', code)
        if 'input = geput.input(get)' not in code:
            code_lines = code.splitlines()
            for idx, line in enumerate(code_lines):
                if line.strip().startswith('def '):
                    # Insert 'input = geput.input(get)' after the function definition
                    code_lines.insert(idx + 1, '    input = geput.input(get)')
                    code = '\n'.join(code_lines)
                    break

    return code


def refactor_code(code: str) -> str:
    """Refactor the given code based on the specified requirements."""
    # Ensure code uses Unix line endings
    code = code.replace('\r\n', '\n').replace('\r', '\n')

    if re.search(r'^@arg', code, flags=re.MULTILINE) or re.search(r'^\s*main\.run\((\w+)\)$', code, flags=re.MULTILINE):
        logger.info("Applying Part 1 transforms")
        code = apply_part1_transforms(code)
    if re.search(r'\bget\s*:\s*Get\b|\bput\s*:\s*Put\b', code):
        logger.info("Applying Part 2 transforms")
        code = update_io_interface(code)
    return code


def ally_refactor(get: geput.Get, put: geput.Put) -> None:
    """
    Read Python code, apply refactoring transforms, and output the result.
    """
    print = geput.print(put)
    input_code = geput.whole(get)

    refactored_code = refactor_code(input_code)
    print(refactored_code)


def setup_args(arg):
    """Set up the command-line arguments."""
    # No specific arguments needed for this script


if __name__ == "__main__":
    main.go(ally_refactor, setup_args)

"""
TODO: Improve handling of complex code structures and edge cases.
FIXME: Ensure all comments are preserved during refactoring.
"""
