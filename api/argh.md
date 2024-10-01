Here's a comprehensive summary of the Argh API, combining the key points from all the provided inputs:

```markdown
# Argh API Comprehensive Summary

## Core Functions

- `dispatch(parser, argv=None, add_help_command=True, completion=True, pre_call=None, output_file=sys.stdout, errors_file=sys.stderr, raw_output=False, namespace=None, skip_unknown_args=False, kwargs_as_positional=None, name_mapping_policy=None)`: Main entry point for parsing arguments and calling relevant functions
- `dispatch_command(func, *args, **kwargs)`: Dispatch a single command function
- `dispatch_commands(functions, *args, **kwargs)`: Dispatch multiple command functions
- `parse_and_resolve(*args, **kwargs)`: Parse arguments and resolve to endpoint function
- `run_endpoint_function(func, namespace, *args, **kwargs)`: Run resolved endpoint function

## Decorators

- `@arg(*args, **kwargs)`: Add or customize argument for function
- `@expects_obj`: Expect namespace object as first argument
- `@named(name)`: Set custom name for command
- `@aliases(*names)`: Set aliases for command
- `@wrap_errors(errors=None, processor=None, ExceptionClass=CommandError)`: Wrap exceptions

## Classes

- `ArghParser`: Integrates argument parsing and dispatching (subclass of ArgumentParser)
- `EntryPoint`: Decorator to register commands for delayed parsing

## Argument Inference

- Function parameters become CLI arguments
- Type annotations (str, int, float, bool) infer argument types
- `Literal` annotations infer choices
- `list[type]` annotations infer nargs="+" and element type
- Use `Annotated[type, Help("description")]` for help text

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

## Utility Functions

- `confirm(question, default=None)`: Prompt for yes/no confirmation
- `safe_input(prompt)`: Cross-platform safe input function

## Constants

- `PARSER_FORMATTER`: Default formatter for ArgumentParser
- `COMPLETION_ENABLED`: Flag if shell completion is enabled

## Name Mapping Policies

- `NameMappingPolicy.BY_NAME_IF_KWONLY`: Default policy
- `NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT`: Legacy policy

## Exceptions

- `CommandError`: Base exception for command errors
- `AssemblingError`: Error configuring parser
- `DispatchingError`: Error during command dispatch

## Usage Example

```python
import argh

@arg("-p", "--patterns", nargs="*")
def cmd(*, patterns: list[str] | None = None) -> list:
  # Command implementation
  pass

if __name__ == '__main__':
  parser = ArghParser()
  parser.add_commands([cmd])
  parser.dispatch()
```

This summary covers the key components an expert programmer would need to use Argh effectively, including main functions, decorators, classes, argument handling, and usage patterns.
```

This comprehensive summary combines all the important aspects of the Argh API from the various input files, providing a concise yet thorough overview for an expert programmer to work with the library.
