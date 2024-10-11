import os
import sys
from enum import Enum, auto

__version__ = "0.1.3"

class redirect:
    class KEEP:
        pass

    def __init__(self, stdin=KEEP, stdout=KEEP, stderr=KEEP):
        self.redirects = {'stdin': stdin, 'stdout': stdout, 'stderr': stderr}
        self.saved_fds = {}
        self.opened_files = {}

    def __enter__(self):
        for stream, target in self.redirects.items():
            if target is self.KEEP:
                continue
            fd = getattr(sys, stream).fileno()
            self.saved_fds[stream] = os.dup(fd)
            if target is None:
                target = os.devnull
            elif isinstance(target, str):
                file_fd = os.open(target, os.O_RDWR | os.O_CREAT)
                os.dup2(file_fd, fd)
                self.opened_files[stream] = file_fd
            else:
                os.dup2(target.fileno(), fd)

    def __exit__(self, exc_type, exc_value, traceback):
        for stream, fd in self.saved_fds.items():
            os.dup2(fd, getattr(sys, stream).fileno())
            os.close(fd)
        for fd in self.opened_files.values():
            os.close(fd)
