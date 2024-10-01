Here's a compact summary of the Argh API in markdown:

```markdown
# Argh API Summary

## Core Functions

- `dispatch(parser, argv=None, add_help_command=True, completion=True, pre_call=None, output_file=sys.stdout, errors_file=sys.stderr, raw_output=False, namespace=None, skip_unknown_args=False, kwargs_as_positional=None, name_mapping_policy=None)`: Parses arguments and calls the relevant function
- `dispatch_command(function, *args, **kwargs)`: Shortcut for single-command applications
- `dispatch_commands(functions, *args, **kwargs)`: Shortcut to dispatch multiple commands

## Decorators

- `@arg(*args, **kwargs)`: Extends argument declaration
- `@wrap_errors(errors=None, processor=None, ExceptionClass=CommandError)`: Wraps exceptions

## Classes

- `ArghParser`: Integrates argument parsing and dispatching
- `EntryPoint`: Decorator to register commands for delayed parsing

## Argument Inference

- Function parameters become CLI arguments
- Type annotations (str, int, float, bool) infer argument types
- `Literal` annotations infer choices
- `list[type]` annotations infer nargs="+" and element type

## Exceptions

- `CommandError`: For expected errors, hides traceback

## Assembly Functions  

- `add_commands(parser, functions, namespace=None, title=None, description=None, help=None)`
- `set_default_command(parser, function)`

## Function Signatures

- Regular args become positional CLI args
- *args becomes zero-or-more positional args  
- Keyword-only args become optional CLI args
- Boolean keyword-only args become flags

## Return Values

- Strings printed verbatim
- Sequences/generators printed line by line
```

This summary covers the key components and concepts of the Argh API that an expert programmer would need to use the library effectively.

