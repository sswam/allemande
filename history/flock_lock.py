import os
import fcntl
import time

class Filelock:
    """A simple file-based lock using fcntl.flock()"""
    def __init__(self, lockfile, timeout=-1, check_interval=0.1):
        self.lockfile = lockfile
        self.timeout = timeout
        self.check_interval = check_interval
        self.fd = None

    def __enter__(self):
        open_mode = os.O_RDWR | os.O_CREAT | os.O_TRUNC
        self.fd = os.open(self.lockfile, open_mode, 0o600)

        start_time = time.time() if self.timeout > 0 else 0

        while True:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except (IOError, OSError):
                pass
            if self.timeout == 0 or (self.timeout > 0 and time.time() >= start_time + self.timeout):
                break
            time.sleep(self.check_interval)

        os.close(self.fd)
        raise TimeoutError(f"Lock could not be acquired within {self.timeout} seconds: {self.lockfile}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
            os.close(self.fd)
