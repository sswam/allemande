"""
Utility functions
"""


def dict_not_none(d: dict) -> dict:
    """Return a new dict with only the non-None values."""
    return {k: v for k, v in d.items() if v is not None}


def list_not_none(l: list) -> list:
    """Return a new list with only the non-None values."""
    return [v for v in l if v is not None]


def quiet_unless_debug(fn, *args, **kwargs):
    """Quiet stdout and stderr unless in debug mode."""
    # FIXME: Not tested
    if logs.level() <= logs.DEBUG:
        return fn(*args, **kwargs)
    with unix.redirect(stdout=None, stderr=None):
        return fn(*args, **kwargs)
