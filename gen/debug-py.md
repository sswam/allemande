Here are some lesser-known debugging techniques for Python:

1. `breakpoint()` built-in (Python 3.7+)
```python
def my_function():
    breakpoint()  # Drops into pdb debugger
```

2. Post-mortem debugging
```python
import pdb
try:
    # code
except:
    pdb.post_mortem()
```

3. Debug logging with `__repr__`
```python
class MyClass:
    def __repr__(self):
        return f"MyClass(important_attr={self.important_attr})"
```

4. Print stack traces anywhere
```python
import traceback
traceback.print_stack()
```

5. `sys.settrace()` for function call tracing
```python
import sys

def trace_calls(frame, event, arg):
    print(f"{event}: {frame.f_code.co_name}")
    return trace_calls  # Return the trace function to continue tracing

sys.settrace(trace_calls)
```

6. Use `locals()` or `globals()` to inspect variables
```python
print(locals())  # Print all local variables
```

7. `faulthandler` for segfault debugging
```python
import faulthandler
faulthandler.enable()
```

8. `icecream` package for print debugging
```python
from icecream import ic
ic(my_variable)  # Prints both name and value
```

9. Memory profiling with `pympler`
```python
from pympler import asizeof
asizeof.asizeof(my_object)
```

10. Logging with context
```python
import contextlib
import logging

@contextlib.contextmanager
def debug_section(name):
    logging.debug(f"Entering {name}")
    yield
    logging.debug(f"Exiting {name}")
```

11. Debug print with timing
```python
from datetime import datetime
print(f"[{datetime.now()}] Debug: {value}")
```

12. IPython embed
```python
from IPython import embed
embed()  # Opens IPython shell at this point
```

13. Remote debugging with `rpdb`
```python
import rpdb
rpdb.set_trace()
```

14. Using assertions with messages
```python
assert condition, f"Detailed message: {variable}"
```

15. Visual debugging of data structures
```python
import pprint
pprint.pprint(complex_structure)
```

These techniques can be particularly helpful in specific debugging scenarios. Choose based on your specific needs!
