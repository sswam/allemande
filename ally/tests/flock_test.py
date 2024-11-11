import asyncio
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from ally import flock as subject

subject_name = subject.__name__

__version__ = "0.1.2"


def test_filelock_basic():
    """Test basic file lock acquisition."""
    with tempfile.NamedTemporaryFile() as tf:
        with subject.filelock(tf.name):
            assert Path(tf.name).exists()


def test_filelock_nested_path():
    """Test file lock with nested directory path."""
    with tempfile.TemporaryDirectory() as td:
        lock_path = Path(td) / "nested" / "path" / "lock.file"
        with subject.filelock(lock_path):
            assert lock_path.exists()


def test_filelock_timeout():
    """Test file lock timeout behavior."""
    with tempfile.NamedTemporaryFile() as tf:
        with subject.filelock(tf.name):
            with pytest.raises(TimeoutError):
                with subject.filelock(tf.name, timeout=0.1):
                    pass


def test_filelock_concurrent():
    """Test sequential execution of file locks."""
    with tempfile.NamedTemporaryFile() as tf:
        def lock_and_sleep():
            start_time = time.time()
            with subject.filelock(tf.name, timeout=1):
                time.sleep(0.5)  # Sleep for 0.5 seconds
            return time.time() - start_time

        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(lock_and_sleep)
            future2 = executor.submit(lock_and_sleep)

            time1 = future1.result()
            time2 = future2.result()
            total_time = time1 + time2

            # Total time should be at least 1 second (2 * 0.5s)
            assert total_time >= 1.0


@pytest.mark.asyncio
async def test_afilelock_basic():
    """Test basic async file lock acquisition."""
    with tempfile.NamedTemporaryFile() as tf:
        async with subject.afilelock(tf.name):
            assert Path(tf.name).exists()


@pytest.mark.asyncio
async def test_afilelock_timeout():
    """Test async file lock timeout behavior."""
    with tempfile.NamedTemporaryFile() as tf:
        async with subject.afilelock(tf.name):
            with pytest.raises(TimeoutError):
                async with subject.afilelock(tf.name, timeout=0.1):
                    pass


@pytest.mark.asyncio
async def test_afilelock_concurrent():
    """Test sequential execution of async file locks."""
    with tempfile.NamedTemporaryFile() as tf:
        async def lock_and_sleep():
            start_time = time.time()
            async with subject.afilelock(tf.name, timeout=1):
                await asyncio.sleep(0.5)  # Sleep for 0.5 seconds
            return time.time() - start_time

        results = await asyncio.gather(lock_and_sleep(), lock_and_sleep())
        total_time = sum(results)

        # Total time should be at least 1 second (2 * 0.5s)
        assert total_time >= 1.0


def test_filelock_empty_path():
    """Test file lock with empty path."""
    with pytest.raises(Exception):
        with subject.filelock(""):
            pass


@pytest.mark.asyncio
async def test_afilelock_empty_path():
    """Test async file lock with empty path."""
    with pytest.raises(Exception):
        async with subject.afilelock(""):
            pass


def test_filelock_permissions():
    """Test file lock permissions."""
    with tempfile.NamedTemporaryFile() as tf:
        with subject.filelock(tf.name):
            assert oct(os.stat(tf.name).st_mode & 0o777) == oct(0o600)


def test_filelock_cleanup():
    """Test file descriptor cleanup after file lock."""
    with tempfile.NamedTemporaryFile() as tf:
        fd_before = os.dup(1)
        with subject.filelock(tf.name):
            pass
        fd_after = os.dup(1)
        assert fd_after - fd_before == 1
        os.close(fd_before)
        os.close(fd_after)


@pytest.mark.asyncio
async def test_afilelock_cleanup():
    """Test file descriptor cleanup after async file lock."""
    with tempfile.NamedTemporaryFile() as tf:
        fd_before = os.dup(1)
        async with subject.afilelock(tf.name):
            pass
        fd_after = os.dup(1)
        assert fd_after - fd_before == 1
        os.close(fd_before)
        os.close(fd_after)
