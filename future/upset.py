
def upset(name: str, value: Any, level: int = 2) -> None:
    """
    Set a variable in the caller's caller's namespace.
    Claude does not approve of this function, in fact it kind of upsets him.
    """
    frame = sys._getframe(level)
    caller_locals = frame.f_locals
    caller_globals = frame.f_globals
    code = frame.f_code

    if name in code.co_names and name not in caller_globals:
        # Symbol is likely declared as nonlocal
        nonlocal_scope = sys._getframe(level + 1).f_locals
        nonlocal_scope[name] = value
    elif name in code.co_names and name in caller_globals:
        # Symbol is likely declared as global
        caller_globals[name] = value
    else:
        # Regular local variable
        caller_locals[name] = value


def test_upset():
    def outer():
        x = 0
        subject.upset('x', 1)
        assert x == 1
    outer()

def test_upset_2():
    def outer():
        x = 0
        def inner():
            nonlocal x
            subject.upset('x', 1, level=2)  # Changed level from 1 to 2
        inner()
        assert x == 1
    outer()
