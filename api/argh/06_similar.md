# Argh API Summary

```markdown
# Core Functions

`argh.dispatch()`
- Dispatches command(s) to handler function(s)

`argh.parse_and_run()`
- Parses arguments and runs corresponding function

`argh.add_commands(parser, functions, namespace=None)`
- Adds commands to parser from functions

# Decorators

`@arg('--option', '-o')`
- Adds command-line argument to function

`@expects_obj`
- Indicates function expects ArgParser namespace object

`@named(name)`
- Sets alternative name for command function

`@aliases('alias1', 'alias2')`
- Defines aliases for command

# Helper Functions

`argh.confirm(question, default=None)`
- Prompts for yes/no confirmation

`argh.safe_input(prompt)`
- Safe wrapper for input()

# Constants

`PARSER_FORMATTER`
- Default formatter class for ArgumentParser

`COMPLETION_ENABLED`
- Flag indicating shell completion support
```

This summary covers the key components of the Argh API that an expert programmer would need to use the library effectively. It includes the main functions for dispatching and parsing commands, decorators for configuring arguments and commands, and helper functions for user interaction.

