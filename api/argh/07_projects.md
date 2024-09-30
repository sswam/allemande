Here's a compact summary of the Argh API in markdown:

```markdown
# Argh API Summary

## Core Functions

- `@arg(*args, **kwargs)`: Decorator to specify argument details
- `@expects_obj`: Decorator to indicate function expects argparse.Namespace
- `@named(name)`: Decorator to specify function name for dispatch
- `dispatch_command(func, *args, **kwargs)`: Dispatch single command
- `dispatch_commands(functions, *args, **kwargs)`: Dispatch multiple commands

## Parser Configuration

- `ArghParser(*args, **kwargs)`: Customized ArgumentParser 
- `add_commands(parser, functions, namespace=None, title=None, help=None, description=None)`: Add commands to parser

## Utilities

- `confirm(question, default=None)`: Prompt for yes/no confirmation
- `safe_input(prompt)`: Cross-platform input function

## Types

- `CommandError`: Exception for command errors

## Constants

- `PARSER_FORMATTER`: Default formatter class
```

This summary covers the key components an expert programmer would need to use the Argh library effectively, including function prototypes and brief descriptions of their purposes.

