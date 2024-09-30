Here's a compact summary of the Argh API in markdown:

```markdown
# Argh API Summary

## Decorators

### @arg
```python
@arg(*args, **kwargs)
```
Customize argument parsing for a function parameter.

## Functions

### dispatch_command
```python
dispatch_command(func, argv=None, completion=True, pre_call=None, output_file=sys.stdout, errors_file=sys.stderr, raw_output=False, namespace=None, skip_unknown_args=False, old_name_mapping_policy=True)
```
Dispatch a single command function.

## Argument Handling

- Use `nargs="*"` for multiple values per argument
- Default values as lists allow multiple values without `nargs`

## Name Mapping Policy

- Set `old_name_mapping_policy=False` for new behavior

## Example

```python
@arg("-p", "--patterns", nargs="*")
def cmd(*, patterns: list[str] | None = None) -> list:
    # Command implementation
```
```

This summary covers the key aspects of the Argh API as presented in the cookbook, including argument decoration, command dispatch, and handling multiple values per argument.

