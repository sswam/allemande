Here's a compact summary of the key parts of the Argh API in markdown format:

```markdown
# Argh API Summary

## Core Classes

- `ArghParser`: Subclass of ArgumentParser with added Argh functionality
- `EntryPoint`: Object to attach functions to and dispatch as commands

## Key Functions

- `add_commands(parser, functions, ...)`: Add functions as commands to parser
- `dispatch(parser, argv=None, ...)`: Parse args and run command
- `dispatch_command(function, ...)`: Dispatch single function as command
- `dispatch_commands(functions, ...)`: Dispatch multiple functions as commands
- `set_default_command(parser, function, ...)`: Set default command for parser

## Decorators

- `@arg(*args, **kwargs)`: Declare argument for function  
- `@aliases(*names)`: Define alternate command names
- `@named(new_name)`: Set custom command name
- `@wrap_errors(errors=None, processor=None)`: Wrap exceptions

## Other

- `confirm(action, default=None, skip=False)`: Prompt for confirmation
- `COMPLETION_ENABLED`: Flag if shell completion is available
- `autocomplete(parser)`: Add shell completion support

## Exceptions

- `CommandError`: Raised from command, prints message and exits
- `AssemblingError`: Error configuring parser
- `DispatchingError`: Error during command dispatch

## Constants

- `PARSER_FORMATTER`: Default formatter for ArgumentParser
- Various `ATTR_*` constants for function attributes

```

This covers the main classes, functions, decorators and other key elements an expert programmer would need to use the Argh API. Let me know if you need any clarification or additional details on any part of the summary.

