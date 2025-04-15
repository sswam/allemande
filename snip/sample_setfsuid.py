import ctypes
import os
from contextlib import contextmanager


import ctypes
import ctypes.util
import errno
import os

# NOTE: setfsuid is largely deprecated, just use seteuid and don't use threads!


libc_so = ctypes.util.find_library('c')
libc = ctypes.CDLL(libc_so, use_errno=True)


def setfsuid(fsuid):
    """Set user identity used for filesystem checks. See setfsuid(2)."""
    # Per the BUGS section in setfsuid(2), you can't really tell if a
    # setfsuid call succeeded. As a hack, we can rely on the fact that
    # setfsuid returns the previous fsuid and call it twice. The result
    # of the second call should be the desired fsuid.
    libc.setfsuid(ctypes.c_int(fsuid))
    new_fsuid = libc.setfsuid(ctypes.c_int(fsuid))

    # Fake an EPERM even if errno was not set when we can detect that
    # setfsuid failed.
    err = errno.EPERM if new_fsuid != fsuid else ctypes.get_errno()
    if err:
        raise OSError(err, os.strerror(err))


# TODO we also need setfsgid to CHATUSER_GID (env var)


# Following code, change to use setfsuid above

# Linux syscall numbers (x86_64)
SYS_setfsuid = 138
libc = ctypes.CDLL(None)

@contextmanager
def temp_fsuid(uid):
    old_fsuid = libc.syscall(SYS_setfsuid, -1)  # get current fsuid
    try:
        libc.syscall(SYS_setfsuid, uid)
        yield
    finally:
        libc.syscall(SYS_setfsuid, old_fsuid)



async def serve_file(user_id, path):
    # Synchronous open with correct fsuid
    with set_fsuid(user_id):
        fd = open(path, 'rb')

    # Once opened, can serve asynchronously
    async with aiofiles.wrap(fd) as file:
        # Stream chunks async
        while chunk := await file.read(8192):
            yield chunk

