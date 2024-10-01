The `__format__()` special method in Python is used to define custom string formatting for objects. It's called by the `format()` built-in function and string `format()` method. The method signature is:

```python
def __format__(self, format_spec):
    # Custom formatting logic
    return formatted_string
```

The `format_spec` parameter is a string that specifies how the object should be formatted. You can define your own formatting rules based on this spec.

Example usage:

```python
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __format__(self, format_spec):
        if format_spec == 'p':
            return f'({self.x}, {self.y})'
        return f'{self.x},{self.y}'

p = Point(1, 2)
print(f'{p:p}')  # Output: (1, 2)
print(f'{p}')    # Output: 1,2
```

