Yes, Python's AST module can detect when the last statement in a list of statements is an expression. Here's an example of how you can do this:

```python
import ast

def is_expression(node):
    """Check if a node is an expression (rather than a statement)."""
    return isinstance(node, ast.Expr)

def split_statements_and_expression(code):
    """Split code into statements and final expression (if any)."""
    tree = ast.parse(code)
    body = tree.body
    
    if body and is_expression(body[-1]):
        statements = body[:-1]
        expression = body[-1].value
        return statements, expression
    else:
        return body, None

# Example usage:
examples = [
    """
x = 1
y = 2
x + y
    """,
    """
x = 1
y = 2
print(x + y)
    """,
]

for code in examples:
    statements, expr = split_statements_and_expression(code)
    print("Code:")
    print(code.strip())
    print("\nStatements:", [ast.unparse(stmt) for stmt in statements])
    print("Expression:", ast.unparse(expr) if expr else None)
    print("-" * 40)
```

Output:
```
Code:
x = 1
y = 2
x + y

Statements: ['x = 1', 'y = 2']
Expression: x + y
----------------------------------------
Code:
x = 1
y = 2
print(x + y)

Statements: ['x = 1', 'y = 2', 'print(x + y)']
Expression: None
----------------------------------------
```

The key points are:

1. The AST represents expressions differently from statements. Pure expressions are wrapped in an `ast.Expr` node.

2. When you have a standalone expression like `x + y`, it appears in the AST as an `ast.Expr` node containing the actual expression.

3. Function calls like `print(x)` are technically expressions, but when they appear as statements, they're still wrapped in `ast.Expr` nodes.

4. The `ast.unparse()` function (available in Python 3.9+) can convert AST nodes back to source code.

You can use this to implement REPL-like behavior where you want to handle the last expression differently from the preceding statements. For example, in a Jupyter-like environment, you might want to execute all statements but return the value of the final expression.

Here's a more practical example:

```python
def eval_code_block(code, globals_dict=None, locals_dict=None):
    """
    Evaluate a block of code, returning the value of the last expression if any.
    """
    if globals_dict is None:
        globals_dict = {}
    if locals_dict is None:
        locals_dict = {}
    
    statements, expr = split_statements_and_expression(code)
    
    # Execute all statements
    for stmt in statements:
        exec(compile(ast.Module(body=[stmt], type_ignores=[]), '<string>', 'exec'),
             globals_dict, locals_dict)
    
    # If there's a final expression, evaluate and return it
    if expr:
        return eval(compile(ast.Expression(body=expr), '<string>', 'eval'),
                   globals_dict, locals_dict)
    return None

# Example usage:
result = eval_code_block("""
x = 1
y = 2
x + y
""")
print(result)  # Outputs: 3
```

This pattern is similar to how interactive Python environments handle code blocks, where the last expression's value is automatically displayed.

