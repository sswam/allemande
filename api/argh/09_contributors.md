Here's a compact summary of the Argh API in markdown:

```markdown
# Argh API Summary

## Key Functions

- `argh.dispatch(functions, *args, **kwargs)`: Main entry point for dispatching commands
- `argh.arg(*args, **kwargs)`: Decorator to specify argument properties
- `argh.expects_obj(func)`: Decorator to indicate function expects args as object
- `argh.named(name)`: Decorator to specify command name  

## Parser Configuration

- `argh.ArghParser(**kwargs)`: Custom ArgumentParser subclass
- `parser.add_commands(functions, namespace=None, title=None, help=None, description=None)`: Add commands to parser

## Dispatching

- `dispatch_command(function, *args, **kwargs)`: Dispatch single command
- `dispatch_commands(functions, *args, **kwargs)`: Dispatch multiple commands

## Utilities  

- `argh.confirm(prompt, default=None)`: Prompt user for confirmation
- `argh.safe_input(prompt)`: Cross-platform safe input function

## Decorators

- `@arg()`: Specify argument properties 
- `@command`: Mark function as command
- `@wrap_errors(*exceptions)`: Catch and wrap specified exceptions

## Types

- `CommandRunner`: Abstract base class for command runners
```

This covers the key components an expert programmer would need to use the Argh API effectively. Let me know if you need any clarification or additional details.

