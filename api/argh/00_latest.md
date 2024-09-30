Here's a compact summary of the Argh API in markdown:

```markdown
# Argh API Summary

## Core Functions

- `dispatch_command(func, *args, **kwargs)`: Dispatch a single command function
- `dispatch_commands(commands, *args, **kwargs)`: Dispatch multiple command functions

## Decorators

- `@arg('name', [options])`: Add argument to function
- `@expects_obj`: Expect namespace object as first argument
- `@named(name)`: Set custom name for command
- `@aliases(*names)`: Set aliases for command

## Types

- `CommandArguments`: Type for command arguments
- `NamespaceProxy`: Proxy for argparse Namespace

## Helper Functions  

- `set_default_command(func)`: Set default command
- `add_commands(parser, functions, namespace=None)`: Add commands to parser
- `parse_args(parser, args=None, namespace=None)`: Parse arguments

## Constants

- `PARSER_FORMATTER`: Default help formatter
- `COMPLETION_ENABLED`: Flag if shell completion is enabled

## Exceptions

- `CommandError`: Base exception for command errors

## Usage

```python
import argh

def main(args):
    pass

if __name__ == '__main__':
    argh.dispatch_command(main)
```
```

This summary covers the key components an expert programmer would need to use Argh effectively, including the main functions, decorators, types, and usage pattern. Let me know if you need any clarification or additional details!

