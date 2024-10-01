Here's a compact summary of the Argh API in markdown:

```markdown
# Argh API Summary

## Core Functions

- `argh.dispatch_command(func)`: Dispatches a single command
- `argh.dispatch_commands(funcs)`: Dispatches multiple commands

## Function Annotations

- Use standard Python type hints
- `Annotated[type, Help("description")]`: Add help text
- `Literal["option1", "option2"]`: Define choices

## Argument Inference

- Positional args: Regular function parameters
- Optional args: Keyword-only parameters
- Types: Inferred from type hints
- Defaults: Inferred from default values
- Actions: Inferred (e.g. `bool` becomes `store_true`)

## Function Signature

```python
def command(
    positional: Annotated[str, Help("description")],
    *,
    option: Literal["a", "b"] = "a",
    flag: bool = False
) -> ReturnType:
    ...

argh.dispatch_command(command)
```

- No decorators required
- Regular callable Python function
- Type hints provide CLI metadata
- Keyword-only args become options
```

This summary covers the key aspects of using Argh to create CLI interfaces, focusing on the latest API design that leverages type hints and eliminates decorators.

