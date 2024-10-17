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

__version__ = "0.1.4"


def test_get_logger():
    logger = subject.get_logger()
    assert logger.name == 'logs_test'


def test_get_log_level():
    with patch(f'{subject_name}.get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_handler = MagicMock()
        mock_handler.level = 20  # INFO level
        mock_logger.handlers = [mock_handler]
        mock_get_logger.return_value = mock_logger

        assert subject.get_log_level() == 'INFO'


@patch('os.makedirs')
@patch('logging.FileHandler')
@patch('logging.StreamHandler')
@patch('os.chmod')
def test_setup_logging(mock_chmod, mock_stream_handler, mock_file_handler, mock_makedirs):
    """
    Test the setup_logging function to ensure it configures logging correctly.
    """
    mock_logger = MagicMock()
    with patch(f'{subject_name}.get_logger', return_value=mock_logger):
        subject.setup_logging('test_module', 'DEBUG')

    mock_makedirs.assert_called_once_with(os.path.expanduser("~/.logs"), exist_ok=True, mode=0o700)
    mock_file_handler.assert_called_once()
    mock_stream_handler.assert_called_once()
    mock_logger.debug.assert_called_with("Starting test_module")
    mock_chmod.assert_called_once()


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
        assert "1, b=2" in text
