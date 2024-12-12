"""A thread-safe dictionary implementation using a mutex lock."""

from threading import Lock
from typing import TypeVar, Any, Iterator

KT = TypeVar('KT')  # Key Type
VT = TypeVar('VT')  # Value Type

class ThreadSafeDict:
    """A thread-safe dictionary implementation using a mutex lock."""

    def __init__(self, *args, **kwargs):
        self._lock = Lock()
        self._dict: dict[Any, Any] = dict(*args, **kwargs)

    def __getitem__(self, key: KT) -> VT:
        with self._lock:
            return self._dict[key]

    def __setitem__(self, key: KT, value: VT) -> None:
        with self._lock:
            self._dict[key] = value

    def __delitem__(self, key: KT) -> None:
        with self._lock:
            del self._dict[key]

    def __len__(self) -> int:
        with self._lock:
            return len(self._dict)

    def __contains__(self, key: KT) -> bool:
        with self._lock:
            return key in self._dict

    def get(self, key: KT, default: VT|None = None) -> VT|None:
        with self._lock:
            return self._dict.get(key, default)

    def pop(self, key: KT, default: VT|None = None) -> VT|None:
        with self._lock:
            if default is None:
                return self._dict.pop(key)
            return self._dict.pop(key, default)

    def clear(self) -> None:
        with self._lock:
            self._dict.clear()

    def update(self, *args, **kwargs) -> None:
        with self._lock:
            self._dict.update(*args, **kwargs)

    def keys(self) -> list:
        with self._lock:
            return list(self._dict.keys())

    def values(self) -> list:
        with self._lock:
            return list(self._dict.values())

    def items(self) -> list:
        with self._lock:
            return list(self._dict.items())

    def copy(self) -> dict:
        with self._lock:
            return self._dict.copy()

    def __iter__(self) -> Iterator[KT]:
        with self._lock:
            # Return a list of keys to avoid holding the lock during iteration
            return iter(list(self._dict))

    def __str__(self) -> str:
        with self._lock:
            return str(self._dict)

    def __repr__(self) -> str:
        with self._lock:
            return f"ThreadSafeDict({repr(self._dict)})"


# This implementation:
#
# 1. Uses a `threading.Lock()` to protect all access to the underlying dictionary
# 2. Implements the most common dictionary methods
# 3. Makes sure all operations are atomic by using the lock
# 4. Returns copies of collections (keys, values, items) to ensure thread safety after the method returns
# 5. Supports basic dictionary operations like getting, setting, deleting items
# 6. Includes support for iteration (though it makes a copy of the keys to avoid holding the lock during iteration)
#
# Key features:
# - Thread-safe access to all dictionary operations
# - Implements most common dictionary methods
# - Simple to use, with similar interface to regular dict
# - Type hints for better IDE support
#
# Limitations:
# - Not as performant as a regular dict due to lock overhead
# - Doesn't implement absolutely every dict method (but can be extended as needed)
# - Makes copies of collections when returning them, which uses more memory
# - Iterator methods return lists instead of views

# You can use this ThreadSafeDict just like a regular dict, but it will be safe to use from multiple threads.

# Remember that while individual operations are thread-safe, sequences of operations still need external synchronization if they need to be atomic together.
