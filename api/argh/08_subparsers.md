Here's a compact summary of the Argh API for subparsers in markdown:

```markdown
# Argh Subparser API

## Key Classes
- `ArghParser()`: Wrapper around argparse.ArgumentParser

## Methods
- `ArghParser.add_commands([func1, func2], group_name=None)`: Add command functions as subparsers
- `ArghParser.dispatch()`: Parse arguments and call appropriate function

## Standalone Functions
- `argh.assembling.add_commands(parser, functions, namespace=None, title=None, description=None, help=None)`: Add commands to parser
- `argh.dispatching.dispatch(parser, argv=None, add_help_command=True, completion=True, pre_call=None, output_file=sys.stdout, errors_file=sys.stderr, raw_output=False, namespace=None, skip_unknown_args=False)`: Parse args and dispatch to function

## Usage
```python
parser = ArghParser()
parser.add_commands([func1, func2])
parser.dispatch()
```

Creates subparsers for `func1` and `func2`. Use `group_name` parameter to create nested subparser groups.
```
```

