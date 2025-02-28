#!/usr/bin/env python3

# For the main task of detecting the system Python version rather than hard-coding Python 3.8, I need to modify the test code to use the actual Python version. I'll also fix the other issues that pylint reported.
#
# Here's the updated `venv_move_test.py`:


"""Test suite for venv_move module."""

import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Generator
import pytest

import venv_move as subject

subject_name = subject.__name__


def run_command(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run a command and return the completed process"""
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


@pytest.fixture
def temp_venv() -> Generator[Path, None, None]:
    """Create a temporary venv for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "testvenv"
        run_command([sys.executable, "-m", "venv", str(venv_path)])
        yield venv_path


@pytest.fixture
def populated_venv(temp_venv: Path) -> Generator[Path, None, None]:  # pylint: disable=redefined-outer-name
    """Create a temporary venv with some packages installed"""
    pip = temp_venv / "bin" / "pip"
    run_command([str(pip), "install", "requests", "pytest"])
    yield temp_venv


def test_verify_venv_nonexistent():
    """Test verify_venv with non-existent directory"""
    assert not subject.verify_venv("/nonexistent/path")


def test_verify_venv_empty_dir():
    """Test verify_venv with empty directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        assert not subject.verify_venv(tmpdir)


def test_verify_venv_valid(temp_venv):  # pylint: disable=redefined-outer-name
    """Test verify_venv with valid venv"""
    assert subject.verify_venv(str(temp_venv))


def test_venv_move_basic(populated_venv):  # pylint: disable=redefined-outer-name
    """Test basic venv move functionality"""
    # Create a new location for the venv
    new_location = populated_venv.parent / "moved_venv"
    shutil.copytree(populated_venv, new_location)

    # Move the venv
    subject.venv_move(str(new_location), yes=True)

    # Test that python still works in the moved venv
    python = new_location / "bin" / "python"
    result = run_command([str(python), "-c", "import requests; print('success')"])
    assert "success" in result.stdout


def test_venv_move_with_pycache(populated_venv):  # pylint: disable=redefined-outer-name
    """Test venv move with __pycache__ directories"""
    # Create some __pycache__ directories
    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    cache_dir = populated_venv / "lib" / python_version / "site-packages" / "__pycache__"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "test.pyc").touch()

    new_location = populated_venv.parent / "moved_venv"
    shutil.copytree(populated_venv, new_location)

    # Move the venv with pycache removal
    subject.venv_move(str(new_location), remove_pycache=True, yes=True)

    # Verify __pycache__ was removed
    assert not list(new_location.rglob("__pycache__"))


def test_venv_move_keep_pycache(populated_venv):  # pylint: disable=redefined-outer-name
    """Test venv move while keeping __pycache__ directories"""
    # Create some __pycache__ directories
    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    cache_dir = populated_venv / "lib" / python_version / "site-packages" / "__pycache__"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "test.pyc").touch()

    new_location = populated_venv.parent / "moved_venv"
    shutil.copytree(populated_venv, new_location)

    # Move the venv without pycache removal
    subject.venv_move(str(new_location), remove_pycache=False, yes=True)

    # Verify __pycache__ still exists
    assert list(new_location.rglob("__pycache__"))


def test_venv_move_pip_still_works(populated_venv):  # pylint: disable=redefined-outer-name
    """Test that pip still works after moving the venv"""
    new_location = populated_venv.parent / "moved_venv"
    shutil.copytree(populated_venv, new_location)

    subject.venv_move(str(new_location), yes=True)

    # Try installing a new package
    pip = new_location / "bin" / "pip"
    result = run_command([str(pip), "install", "pyyaml"])
    assert "Successfully installed" in result.stdout


def test_venv_move_invalid_venv():
    """Test moving an invalid venv"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="Invalid virtual environment"):
            subject.venv_move(tmpdir)


def test_venv_move_same_location(populated_venv):  # pylint: disable=redefined-outer-name
    """Test moving venv to same location"""
    # Should not make any changes
    subject.venv_move(str(populated_venv), yes=True)

    # Verify python still works
    python = populated_venv / "bin" / "python"
    result = run_command([str(python), "-c", "import requests; print('success')"])
    assert "success" in result.stdout
