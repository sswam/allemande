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

import ally.main as subject
import ally.logs
import ally.opts
import ally.geput

subject_name = subject.__name__

__version__ = "0.1.4"

@patch('ally.logs.setup_logging')
@patch('ally.opts._open_files')
@patch('ally.geput.setup_put')
@patch('ally.geput.setup_get')
@patch('argparse.ArgumentParser.parse_args')
def test_go(mock_parse_args, mock_setup_get, mock_setup_put, mock_open_files, mock_setup_logging):
    def mock_main_function(get, put, log_level):
        pass

    mock_setup_args = MagicMock()
    mock_args = argparse.Namespace()
    mock_args.log_level = 'DEBUG'
    mock_args.istream = MagicMock()
    mock_args.ostream = MagicMock()
    mock_parse_args.return_value = mock_args

    mock_setup_get.return_value = MagicMock()
    mock_setup_put.return_value = MagicMock()

    with patch('sys.exit') as mock_exit:
        subject.go(mock_main_function, mock_setup_args)

    mock_setup_args.assert_called_once()
    mock_parse_args.assert_called_once()
    mock_open_files.assert_called_once()
    mock_setup_logging.assert_called_once()
    mock_setup_get.assert_called_once()
    mock_setup_put.assert_called_once()
    mock_exit.assert_not_called()
