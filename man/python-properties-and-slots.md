Here's a concise example of using properties and slots in Python:

```python
class Person:
    __slots__ = ['_name', '_age']

    def __init__(self, name, age):
        self._name = name
        self._age = age

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self._name = value

    @property
    def age(self):
        return self._age

    @age.setter
    def age(self, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError("Age must be a non-negative integer")
        self._age = value

# Usage
p = Person("Alice", 30)
print(p.name)  # Alice
p.age = 31
print(p.age)  # 31
p.name = "Bob"
# p.salary = 50000  # Raises AttributeError due to __slots__
```

This example demonstrates properties for controlled attribute access and `__slots__` for memory optimization and restricting attribute creation.

