from typing import Generic, TypeVar

T = TypeVar('T')

class Get(Generic[T]):
    def __init__(self, value: T):
        self.value = value

    def get(self) -> T:
        return self.value

# Usage
string_get = Get[str]("Hello")
bytes_get = Get[bytes](b"World")


# TODO what I actually want is Get[str] to be equal to Callable[[], Coroutine[None, None, str | None]]

# The TODO you mentioned is indeed possible, but it requires a different approach than what you've shown in the initial code. To achieve what you want, where `Get[str]` is equivalent to `Callable[[], Coroutine[None, None, str | None]]`, you'll need to use a custom type alias or a more complex Generic class. Here's how you can do it:

from typing import Callable, Coroutine, TypeVar, Union

T = TypeVar('T')

# Define Get as a type alias
Get = Callable[[], Coroutine[None, None, Union[T, None]]]

# Usage example
async def get_string() -> str | None:
    return "Hello"

string_get: Get[str] = get_string

# Or, if you prefer a class-based approach:
from typing import Generic, AsyncGenerator

class Get(Generic[T]):
    async def __call__(self) -> T | None:
        ...

    def __class_getitem__(cls, item):
        return Callable[[], Coroutine[None, None, Union[item, None]]]

# Usage example
string_get: Get[str]

# In the first approach, we define `Get` as a type alias that matches your requirements. This is simpler and more straightforward.
# 
# In the second approach, we define `Get` as a class with a custom `__class_getitem__` method. This method is called when you use the square bracket notation (`Get[str]`), and it returns the type you want.
# 
# Both approaches achieve what you're looking for, where `Get[str]` is equivalent to `Callable[[], Coroutine[None, None, str | None]]`.
# 
# Choose the approach that best fits your use case and coding style. The type alias is simpler and more direct, while the class-based approach gives you more flexibility if you need to add methods or attributes to `Get`.
