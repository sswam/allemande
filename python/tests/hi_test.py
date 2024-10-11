import os
import sys
import pytest
import subprocess
import io
from unittest.mock import patch, MagicMock
import logging

import hi as subject

subject_name = subject.__name__

@pytest.fixture
def mock_environ():
    with patch.dict(os.environ, clear=True) as mock_env:
        yield mock_env

def test_hi_function():
    output = io.StringIO()
    subject.hi(put=output.write, name="Test")
    assert output.getvalue().strip() == "Hello, Test"

def test_hi_default_name():
    output = io.StringIO()
    subject.hi(put=output.write)
    assert output.getvalue().strip() == "Hello, World"

def test_command_line_invocation():
    result = subprocess.run(["python", f"{subject_name}.py"], capture_output=True, text=True)
    assert result.stdout.strip() == "Hello, World"

def test_command_line_with_name():
    result = subprocess.run(["python", f"{subject_name}.py", "--name", "CLI"], capture_output=True, text=True)
    assert result.stdout.strip() == "Hello, CLI"

def test_module_invocation():
    fake_out = io.StringIO()
    subject.hi(put=fake_out.write)
    assert fake_out.getvalue().strip() == "Hello, World"

@pytest.mark.parametrize("log_level", ["DEBUG", "INFO", "WARNING"])
def test_log_level_option(log_level):
    result = subprocess.run(["python", f"{subject_name}.py", "--log-level", log_level], capture_output=True, text=True)
    assert log_level in result.stderr

def test_log_level_option_quiet():
    result = subprocess.run(["python", f"{subject_name}.py", "-q"], capture_output=True, text=True)
    assert result.stderr.strip() == "This is an ERROR message\nThis is a CRITICAL message"

def test_log_level_option_verbose():
    result = subprocess.run(["python", f"{subject_name}.py", "-v"], capture_output=True, text=True)
    assert "INFO" in result.stderr

def test_get_logger():
    logger = logs.get_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == f"{subject_name}"

def get_last_n_lines(file_path, n):
    with open(file_path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        block = 1024
        data = []
        remaining_lines = n
        while remaining_lines > 0 and size > 0:
            if size - block < 0:
                block = size
            size -= block
            f.seek(size, os.SEEK_SET)
            buffer = f.read(block)
            data.insert(0, buffer)
            remaining_lines -= buffer.count(b'\n')
        content = b''.join(data)
        return content.decode('utf-8').splitlines()[-n:]

def test_log_file_creation():
    log_file = os.path.expanduser(f"~/.logs/{subject_name}.log")
    if os.path.exists(log_file):
        os.remove(log_file)

    process = subprocess.Popen(["python", f"{subject_name}.py", "--log-level", "DEBUG"])
    pid = process.pid
    process.wait()

    assert os.path.exists(log_file)

    log_lines = get_last_n_lines(log_file, 10)

    # Check that the log entry is one of the last entries based on PID
    relevant_lines = [line for line in log_lines if f"PID:{pid}" in line]
    assert any(f"DEBUG     {subject_name}  This is a DEBUG message" in line for line in relevant_lines)
