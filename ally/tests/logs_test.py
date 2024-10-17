import os
import io
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import logging
import argparse

import ally.logs as subject

subject_name = subject.__name__

__version__ = "0.1.6"


def test_setup_logging():
    """
    Test the setup_logging function to ensure it configures logging correctly.
    """
    with patch(f'{subject_name}.get_logger') as mock_get_logger:
        subject.setup_logging()

    mock_get_logger.assert_called_once_with(root=True)

def test_get_logger():
    logger = subject.get_logger()
    assert logger.name == 'logs_test'
    assert len(logger.handlers) > 0
    assert isinstance(logger.handlers[0], logging.StreamHandler)

    # Check if file handlers are created
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) > 0

    # Check log directory creation
    log_dir = os.path.expanduser("~/.logs")
    assert os.path.exists(log_dir)

    # Check file permissions
    for handler in file_handlers:
        assert os.stat(handler.baseFilename).st_mode & 0o777 == 0o600

def test_get_log_level():
    with patch(f'{subject_name}.get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_handler = MagicMock()
        mock_handler.level = 20  # INFO level
        mock_logger.handlers = [mock_handler]
        mock_get_logger.return_value = mock_logger

        assert subject.get_log_level() == 'INFO'

def test_IndentLogger():
    mock_logger = MagicMock()
    indent_logger = subject.IndentLogger(mock_logger)

    indent_logger.debug("Test message")
    mock_logger.debug.assert_called_with("Test message")

    indent_logger.indent(1)
    indent_logger.debug("Indented message")
    mock_logger.debug.assert_called_with("\tIndented message")

def test_add_context():
    try:
        with subject.add_context("wizerd 831"):
            raise ValueError("Your values are questionable.")
    except ValueError as e:
        text = str(e)
        assert "Your values are questionable." in text
        assert "wizerd 831" in text

def test_context():
    @subject.context("wizerd 831")
    def test_function(a, b=1):
        raise ValueError("Your values are questionable.")

    try:
        test_function(1, b=2)
    except ValueError as e:
        text = str(e)
        assert "Your values are questionable." in text
        assert "wizerd 831" in text
        assert "a: 1" in text
        assert "b: 2" in text

def test_format_args_kwargs():
    args = (1, 2, 3)
    kwargs = {'a': 'x', 'b': 'y'}
    result = subject.format_args_kwargs(args, kwargs)
    assert result == "1, 2, 3, a=x, b=y"

    result_long = subject.format_args_kwargs(args, kwargs, long=True)
    assert result_long == "1\n2\n3\na: x\nb: y\n"

    arg_names = ['x', 'y', 'z']
    result_named = subject.format_args_kwargs(args, kwargs, arg_names=arg_names)
    assert result_named == "x=1, y=2, z=3, a=x, b=y"
