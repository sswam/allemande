Here's a compact summary of the Argh API in markdown format:

```markdown
# Argh API Summary

## Core Functions

- `dispatch(functions, *args, **kwargs)`: Main entry point to dispatch commands
- `parse_and_resolve(*args, **kwargs)`: Parse arguments and resolve to endpoint function
- `run_endpoint_function(func, namespace, *args, **kwargs)`: Run resolved endpoint function

## Decorators

- `@arg(*args, **kwargs)`: Define argument attributes
- `@expects_obj`: Mark function as expecting namespace object 
- `@wrap_errors(*errors)`: Wrap specified errors

## Classes

- `ArghParser`: Subclass of argparse.ArgumentParser
- `EntryPoint`: Define entry point for command assembly

## Helper Functions  

- `add_commands(parser, functions, *args, **kwargs)`: Add commands to parser
- `add_subcommands(parser, functions, *args, **kwargs)`: Add subcommands to parser
- `set_default_command(parser, function)`: Set default command

## Name Mapping Policies

- `NameMappingPolicy.BY_NAME_IF_KWONLY`: Default policy
- `NameMappingPolicy.BY_NAME_IF_HAS_DEFAULT`: Legacy policy

## Key Parameters

- `name_mapping_policy`: Control argument name mapping
- `skip_unknown_args`: Skip unknown arguments
- `add_help_command`: Add help as a command (deprecated)
```

This covers the main components an expert programmer would need to use the Argh API effectively. Let me know if you need any clarification or additional details on specific parts.

