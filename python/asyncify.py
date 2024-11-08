#!/usr/bin/env python3-allemande

"""
This module transforms a non-async Python program into an async version.
"""

import ast
import astor
import sys
from typing import Any, Callable

class AsyncTransformer(ast.NodeTransformer):
    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        # Transform regular functions to async functions
        node.decorator_list.append(ast.Name(id='staticmethod', ctx=ast.Load()))
        node = ast.AsyncFunctionDef(
            name=node.name,
            args=node.args,
            body=node.body,
            decorator_list=node.decorator_list,
            returns=node.returns
        )
        return self.generic_visit(node)

    def visit_For(self, node: ast.For) -> Any:
        # Transform for loops to async for loops
        return ast.AsyncFor(
            target=node.target,
            iter=node.iter,
            body=node.body,
            orelse=node.orelse
        )

    def visit_With(self, node: ast.With) -> Any:
        # Transform with statements to async with statements
        return ast.AsyncWith(
            items=node.items,
            body=node.body
        )

    def visit_Call(self, node: ast.Call) -> Any:
        # Add 'await' to function calls
        return ast.Await(value=node)

    def visit_Import(self, node: ast.Import) -> Any:
        # Replace 'requests' with 'aiohttp'
        for alias in node.names:
            if alias.name == 'requests':
                return ast.Import(names=[ast.alias(name='aiohttp', asname=None)])
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        # Replace 'socket' imports with 'asyncio' equivalents
        if node.module == 'socket':
            return ast.ImportFrom(module='asyncio', names=[ast.alias(name='StreamReader', asname=None), ast.alias(name='StreamWriter', asname=None)], level=0)
        return node

def transform_to_async(source_code: str) -> str:
    tree = ast.parse(source_code)
    transformer = AsyncTransformer()
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    return astor.to_source(transformed_tree)

def main(input_file: str, output_file: str) -> None:
    with open(input_file, 'r') as f:
        source_code = f.read()

    transformed_code = transform_to_async(source_code)

    with open(output_file, 'w') as f:
        f.write(transformed_code)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: asyncify <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    main(input_file, output_file)

# TODOs:
# 1. Handle generator functions and transform them to async generators
# 2. Add support for asyncio.yield in pure functions that might be slow
# 3. Improve handling of library-specific transformations (e.g., more socket operations)
# 4. Add error handling and logging for better debugging
# 5. Implement a more sophisticated method to determine which functions should be made async
# 6. Handle cases where 'await' might be added unnecessarily (e.g., in pure functions)
# 7. Add support for transforming class methods to async methods
# 8. Implement a way to preserve original comments and formatting
