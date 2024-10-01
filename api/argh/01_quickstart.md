Here's a compact summary of the Argh API in markdown:

```markdown
# Argh API Summary

## Core Functions

- `argh.dispatch_command(func, old_name_mapping_policy=False)`: Dispatches a single command
- `argh.dispatch_commands([func1, func2, ...])`: Dispatches multiple commands

## Function Annotations

- Use type hints for automatic argument parsing
- `def func(arg: int)`: Positional argument
- `def func(*, arg: int)`: Named argument/option

## Argument Types

- Positional: Left of `*` in function signature
- Named/Options: Right of `*` in function signature

## Function Return Handling

- `return`: Supported
- `print`: Supported (TBC)
- `yield`: Supported (TBC)

## Advanced Features (Details in Tutorial)

- Custom argument help
- Parser customization
- DRY principles
- Custom command names/aliases
- Value type conversion
- Namespace object usage

## Notes

- Commands are regular Python functions
- Supports loose coupling of components
- Pythonic approach, minimal boilerplate
```

This summary covers the key points an expert programmer would need to use Argh effectively, including function signatures, dispatching commands, argument types, and advanced features to explore in the tutorial.

