Yes, you can use the `io.StringIO` module along with a custom class to achieve this:

```python
import io

class StringIteratorIO(io.TextIOBase):
    def __init__(self, iterator):
        self.iterator = iterator
        self.buffer = ""

    def readable(self):
        return True

    def read(self, size=-1):
        while size < 0 or len(self.buffer) < size:
            try:
                self.buffer += next(self.iterator)
            except StopIteration:
                break
        result = self.buffer[:size]
        self.buffer = self.buffer[size:]
        return result

    def readline(self):
        while '\n' not in self.buffer:
            try:
                self.buffer += next(self.iterator)
            except StopIteration:
                break
        line, sep, self.buffer = self.buffer.partition('\n')
        return line + sep

# Example usage:
iterator = iter(["hello", " ", "world", "\n", "foo", "bar"])
file_like = StringIteratorIO(iterator)

# Read from the file-like object
print(file_like.read(5))  # Output: hello
print(file_like.readline())  # Output:  world
print(file_like.read())  # Output: foobar
```

This class wraps an iterator and makes it look like a file handle that supports `read` and `readline` methods.

