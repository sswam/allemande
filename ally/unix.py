"""Redirect standard streams to /dev/null, a file, or a file-like object, at the UNIX file descriptor level."""

import os
import sys

__version__ = "0.1.5"


class redirect:
    """Redirect standard streams to /dev/null, a file, or a file-like object."""

    class KEEP:
        """Keep the original stream."""

    def __init__(self, stdin=KEEP, stdout=KEEP, stderr=KEEP):
        """Initialize the redirect object."""
        # TODO append option?
        self.redirects = {"stdin": stdin, "stdout": stdout, "stderr": stderr}
        self.saved_fds = {}
        self.opened_files = {}

    def __enter__(self):
        """Apply the redirections."""
        for stream_name, target in self.redirects.items():
            if target is self.KEEP:
                continue
            stream = getattr(sys, stream_name)
            stream.flush()
            fd = stream.fileno()
            self.saved_fds[stream_name] = os.dup(fd)
            if target is None:
                target = os.devnull
                # falls through to the next case, as a string
            if isinstance(target, str):
                mode = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
                if stream_name == "stdin":
                    mode = os.O_RDONLY
                file_fd = os.open(target, mode)
                os.dup2(file_fd, fd)
                self.opened_files[stream_name] = file_fd
            else:
                os.dup2(target.fileno(), fd)

    def __exit__(self, exc_type, exc_value, traceback):
        """Restore original file descriptors and close opened files."""
        for stream_name, fd in self.saved_fds.items():
            stream = getattr(sys, stream_name)
            stream.flush()
            curr_fd = stream.fileno()
            os.dup2(fd, curr_fd)
            os.close(fd)
        for fd in self.opened_files.values():
            os.close(fd)
