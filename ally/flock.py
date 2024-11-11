""" File-based locking using fcntl.flock(), sync and async versions """

import os
import fcntl
import time
import asyncio
import contextlib
from pathlib import Path

__version__ = "0.1.2"


@contextlib.contextmanager
def filelock(lockfile, timeout=-1, check_interval=0.1):
    """
    A file-based lock using fcntl.flock()
    Timeout is in seconds. If timeout is 0, the lock is tried only once.
    If timeout is negative, the lock is tried indefinitely.
    Usage:
    with filelock('lockfile.lock', timeout=10):
        # Protected code here
    """
    fd = None
    try:
        Path(lockfile).parent.mkdir(parents=True, exist_ok=True)
        open_mode = os.O_RDWR | os.O_CREAT | os.O_TRUNC
        fd = os.open(lockfile, open_mode, 0o600)

        start_time = time.time() if timeout > 0 else 0

        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if timeout == 0 or (timeout > 0 and time.time() >= start_time + timeout):
                    raise TimeoutError(
                        f"Lock could not be acquired within {timeout} seconds: {lockfile}"
                    )
                time.sleep(check_interval)

        yield

    finally:
        if fd is not None:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)


@contextlib.asynccontextmanager
async def afilelock(lockfile, timeout=-1, check_interval=0.1):
    """
    An async file-based lock using fcntl.flock()
    Timeout is in seconds. If timeout is 0, the lock is tried only once.
    If timeout is negative, the lock is tried indefinitely.
    Usage:
    async with afilelock('lockfile.lock', timeout=10):
        pass
    """
    fd = None
    try:
        Path(lockfile).parent.mkdir(parents=True, exist_ok=True)
        open_mode = os.O_RDWR | os.O_CREAT | os.O_TRUNC
        fd = os.open(lockfile, open_mode, 0o600)

        start_time = time.time() if timeout > 0 else 0

        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if timeout == 0 or (timeout > 0 and time.time() >= start_time + timeout):
                    raise TimeoutError(
                        f"Lock could not be acquired within {timeout} seconds: {lockfile}"
                    )
                await asyncio.sleep(check_interval)

        yield

    finally:
        if fd is not None:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
