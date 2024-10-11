In python given a function (i.e. var holding a function reference) how can I check if it has a particular named parameter? kwargs or args
Please reply as concise as possible, with no boilerplate or unnecessary explanation.

You can use the `inspect` module to check for specific parameters:

```python
import inspect

def has_parameter(func, param_name):
    return param_name in inspect.signature(func).parameters

# Check for kwargs
has_kwargs = has_parameter(func, '**kwargs')

# Check for args
has_args = has_parameter(func, '*args')
```

This will return `True` if the function has the specified parameter, and `False` otherwise.


How to check for a normal parameter that is either positional or named with default?

You can use the `inspect` module to check for specific parameters:

```python
import inspect

def has_parameter(func, param_name):
    return param_name in inspect.signature(func).parameters

# Check for kwargs
has_kwargs = has_parameter(func, '**kwargs')

# Check for args
has_args = has_parameter(func, '*args')
```

This will return `True` if the function has the specified parameter, and `False` otherwise.

Your approach using the `inspect` module is a good one for checking the presence of parameters in a function. However, to specifically check for a normal parameter that can be either positional or named with a default value, we need to look at the parameter's kind and default value. Here's a more detailed approach:

```python
import inspect

def check_normal_parameter(func, param_name):
    signature = inspect.signature(func)
    if param_name in signature.parameters:
        param = signature.parameters[param_name]
        # Check if it's a normal parameter (POSITIONAL_OR_KEYWORD)
        # and has a default value
        return (param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and
                param.default != inspect.Parameter.empty)
    return False

# Example usage:
def example_func(a, b=2, c=3, *args, **kwargs):
    pass

print(check_normal_parameter(example_func, 'a'))  # False (no default)
print(check_normal_parameter(example_func, 'b'))  # True
print(check_normal_parameter(example_func, 'c'))  # True
print(check_normal_parameter(example_func, 'd'))  # False (doesn't exist)
```

This function does the following:

1. It uses `inspect.signature()` to get the function's signature.
2. It checks if the parameter name exists in the signature.
3. If it exists, it checks two conditions:
   - The parameter kind is `POSITIONAL_OR_KEYWORD`, which means it can be passed either positionally or as a keyword argument.
   - The parameter has a default value (i.e., its default is not `inspect.Parameter.empty`).

This approach will correctly identify parameters that:
- Can be passed either positionally or as keyword arguments
- Have a default value

It will return `False` for:
- Positional-only parameters
- Keyword-only parameters
- Parameters without default values
- `*args` and `**kwargs`
- Non-existent parameters

This method provides a more precise check for the specific type of parameter you're asking about: a normal parameter that can be either positional or named and has a default value.

Here's a concise function to check if a given function accepts **kwargs:

```python
import inspect

def accepts_kwargs(func):
    return any(param.kind == inspect.Parameter.VAR_KEYWORD
               for param in inspect.signature(func).parameters.values())
```

This function returns True if the given function accepts **kwargs, False otherwise.

Here's a concise way to check if a function accepts a catch-all *args parameter:

```python
import inspect

def has_args_parameter(func):
    return any(param.kind == inspect.Parameter.VAR_POSITIONAL for param in inspect.signature(func).parameters.values())
```

Use it like this:

```python
result = has_args_parameter(your_function)
```

This returns True if the function accepts *args, False otherwise.

