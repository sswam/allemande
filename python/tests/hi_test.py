import os
import sys
import pytest
import subprocess
import io
from unittest.mock import patch, MagicMock
import logging

# Add the parent directory to sys.path to import hi and main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hi
from ally import main

@pytest.fixture
def mock_environ():
    with patch.dict(os.environ, clear=True) as mock_env:
        yield mock_env

def test_hi_function():
    output = io.StringIO()
    hi.hi(ostream=output, name="Test")
    assert output.getvalue().strip() == "Hello, Test"

def test_hi_default_name():
    output = io.StringIO()
    hi.hi(ostream=output)
    assert output.getvalue().strip() == "Hello, World"

def test_command_line_invocation():
    result = subprocess.run(["python", "hi.py"], capture_output=True, text=True)
    assert result.stdout.strip() == "Hello, World"

def test_command_line_with_name():
    result = subprocess.run(["python", "hi.py", "--name", "CLI"], capture_output=True, text=True)
    assert result.stdout.strip() == "Hello, CLI"

def test_module_invocation():
    fake_out = io.StringIO()
    hi.hi(ostream=fake_out)
    assert fake_out.getvalue().strip() == "Hello, World"

@pytest.mark.parametrize("log_level", ["DEBUG", "INFO", "WARNING"])
def test_log_level_option(log_level):
    result = subprocess.run(["python", "hi.py", "--log-level", log_level], capture_output=True, text=True)
    assert log_level in result.stderr

def test_log_level_option_quiet():
    result = subprocess.run(["python", "hi.py", "-q"], capture_output=True, text=True)
    assert result.stderr == "This is an ERROR message\nThis is a CRITICAL message\n"

def test_log_level_option_verbose():
    result = subprocess.run(["python", "hi.py", "-v"], capture_output=True, text=True)
    assert "INFO" in result.stderr

def test_get_module_name():
    assert main.get_module_name() == "hi_test"

def test_get_script_name():
    with patch('sys.argv', ['test_script.py']):
        assert main.get_script_name() == "test_script"

def test_get_logger():
    logger = main.get_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "hi_test"

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
    log_file = os.path.expanduser("~/.logs/hi.log")
    if os.path.exists(log_file):
        os.remove(log_file)

    process = subprocess.Popen(["python", "hi.py", "--log-level", "DEBUG"])
    pid = process.pid
    process.wait()

    assert os.path.exists(log_file)

    log_lines = get_last_n_lines(log_file, 10)

    # Check that the log entry is one of the last entries based on PID
    relevant_lines = [line for line in log_lines if f"PID:{pid}" in line]
    assert any("DEBUG     hi  This is a DEBUG message" in line for line in relevant_lines)
