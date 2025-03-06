import os
import io
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Any

import safe_join as subject  # type: ignore

subject_name = subject.__name__

def test_safe_join_basic():
    base = Path("/tmp/test")
    assert subject.safe_join(base, "foo") == Path("/tmp/test/foo").resolve()
    assert subject.safe_join(base, "foo", "bar") == Path("/tmp/test/foo/bar").resolve()

def test_safe_join_parent_traversal():
    base = Path("/tmp/test")
    with pytest.raises(ValueError):
        subject.safe_join(base, "..")
    with pytest.raises(ValueError):
        subject.safe_join(base, "foo/../..")
    with pytest.raises(ValueError):
        subject.safe_join(base, "foo", "..", "..", "etc")

def test_safe_join_absolute():
    base = Path("/tmp/test")
    with pytest.raises(ValueError):
        subject.safe_join(base, "/etc/passwd")
    with pytest.raises(ValueError):
        subject.safe_join(base, "foo", "/etc/passwd")

def test_safe_join_error():
    base = Path("/home/sam/allemande/rooms")
    assert subject.safe_join(base, "cast/Soli.jpg") == Path("/home/sam/allemande/rooms/cast/Soli.jpg").resolve()
