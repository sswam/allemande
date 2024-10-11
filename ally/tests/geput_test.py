import os

# Disable DeprecationWarning https://github.com/jupyter/jupyter_core/issues/398
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"

import io
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import logging
import argparse

import ally.geput as subject

__version__ = "0.1.5"

def test_setup_get_non_tty():
    input_stream = io.StringIO("test input\n")
    get = subject.setup_get(input_stream)

    result = get()
    assert result == "test input"

def test_setup_get_tty():
    with patch('ally.titty.is_tty', return_value=True):
        with patch('ally.titty.get', return_value="tty input"):
            input_stream = io.StringIO()
            get = subject.setup_get(input_stream)

            result = get()
            assert result == "tty input"

def test_setup_put():
    output_stream = io.StringIO()
    put = subject.setup_put(output_stream)

    put("test output")
    assert output_stream.getvalue() == "test output\n"

def test_setup_put_no_newline():
    output_stream = io.StringIO()
    put = subject.setup_put(output_stream)

    put("test output", end="")
    assert output_stream.getvalue() == "test output"

def test_setup_put_multiple_args():
    output_stream = io.StringIO()
    put = subject.setup_put(output_stream)

    put("Hello", "World")
    assert output_stream.getvalue() == "Hello World\n"
