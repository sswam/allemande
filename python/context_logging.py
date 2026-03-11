"""context_logging.py -- Per-task file logging for asyncio services.

Usage:
    At startup:
        context_logging.setup()

    Per request (in the task):
        with context_logging.log_to_file("rooms/foo.log"):
            ...  # all logging in this task goes to the file too

Note: setup() does not change the root logger's level. If it's set above
DEBUG, debug records won't reach this handler. Set it at startup if needed:
    logging.getLogger().setLevel(logging.DEBUG)
"""

import contextlib
import logging
from contextvars import ContextVar
from typing import IO


_log_file: ContextVar[IO | None] = ContextVar("_log_file", default=None)


class ContextFileHandler(logging.Handler):
    """Writes log records to the per-task file set via ContextVar, if any."""

    def emit(self, record: logging.LogRecord) -> None:
        f = _log_file.get()
        if f is None:
            return
        try:
            f.write(self.format(record) + "\n")
            f.flush()
        except Exception:
            self.handleError(record)


@contextlib.contextmanager
def log_to_file(path: str, mode: str = "a"):
    """Context manager: log to *path* for the duration, then restore previous state.

    Safe to nest (uses ContextVar token reset), though only one file is active
    at a time — the inner one wins.
    """
    with open(path, mode) as f:
        token = _log_file.set(f)
        try:
            yield f
        finally:
            _log_file.reset(token)


def setup(level: int = logging.DEBUG) -> None:
    """Install the ContextFileHandler on the root logger. Call once at startup."""
    handler = ContextFileHandler(level)
    # formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
    formatter = logging.Formatter("%(levelname)-8s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
