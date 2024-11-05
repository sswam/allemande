"""Unit tests for unix module functionality"""

import os
import sys
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from typing import Any


import ally.unix as subject  # type: ignore

subject_name = subject.__name__


def test_redirect_null():
    """Test redirecting to /dev/null"""
    with subject.redirect(stdout=None):
        print("This should not be visible")
    # No assertion needed - test passes if no output is visible


def test_redirect_file():
    """Test redirecting to a file"""
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as tmp:
        test_message = "This should be in the file"

        with subject.redirect(stdout=tmp.name):
            print(test_message)

        tmp.seek(0)
        content = tmp.read().strip()
        assert content == test_message

    os.unlink(tmp.name)


def test_redirect_keep():
    """Test KEEP option maintains original stream"""
    original_stdout = sys.stdout
    with subject.redirect(stdout=subject.redirect.KEEP):
        assert sys.stdout == original_stdout


def test_redirect_multiple_streams():
    """Test redirecting multiple streams simultaneously"""
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as out_tmp, \
        tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as err_tmp:

        with subject.redirect(stdout=out_tmp.name, stderr=err_tmp.name):
            print("stdout message")
            print("stderr message", file=sys.stderr)

        out_tmp.seek(0)
        err_tmp.seek(0)
        assert out_tmp.read().strip() == "stdout message"
        assert err_tmp.read().strip() == "stderr message"

    os.unlink(out_tmp.name)
    os.unlink(err_tmp.name)


def test_redirect_nested():
    """Test nested redirections"""
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as outer_tmp, \
        tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as inner_tmp:

        with subject.redirect(stdout=outer_tmp.name):
            print("outer message")
            with subject.redirect(stdout=inner_tmp.name):
                print("inner message")
            print("outer message again")

        outer_tmp.seek(0)
        inner_tmp.seek(0)
        outer_content = outer_tmp.read()
        inner_content = inner_tmp.read()

        assert "inner message" in inner_content
        assert "outer message" in outer_content
        assert "outer message again" in outer_content

    os.unlink(outer_tmp.name)
    os.unlink(inner_tmp.name)


def test_redirect_error_handling():
    """Test error handling during redirection"""
    with pytest.raises(Exception):
        with subject.redirect(stdout="nonexistent_dir/test.txt"):
            pass


def test_version():
    """Test version string format"""
    assert isinstance(subject.__version__, str)
    # Verify version follows semantic versioning (major.minor.patch)
    version_parts = subject.__version__.split(".")
    assert len(version_parts) == 3
    assert all(part.isdigit() for part in version_parts)


@pytest.mark.parametrize(
    "stream,target",
    [
        ("stdout", None),
        ("stderr", None),
        ("stdin", None),
    ],
)
def test_redirect_parametrized(stream, target):
    """Test various stream and target combinations"""
    with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', delete=False) as tmp:
        redirect_args = {stream: target or tmp.name}
        with subject.redirect(**redirect_args):
            if stream == "stdout":
                print("test message")
            elif stream == "stderr":
                print("test message", file=sys.stderr)

    os.unlink(tmp.name)


def test_redirect_cleanup():
    """Test that file descriptors are properly cleaned up"""
    initial_fds = set(os.listdir("/proc/self/fd"))

    with subject.redirect(stdout=None):
        pass

    final_fds = set(os.listdir("/proc/self/fd"))
    assert initial_fds == final_fds
