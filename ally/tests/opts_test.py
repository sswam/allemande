import os
import io
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import logging
import argparse

import ally.opts as subject

subject_name = subject.__name__

__version__ = "0.1.4"


def test_CustomHelpFormatter():
    formatter = subject.CustomHelpFormatter('test')
    assert isinstance(formatter, subject.argparse.HelpFormatter)


def test_setup_logging_args():
    parser = subject.argparse.ArgumentParser()
    subject._setup_logging_args('test_module', parser)
    args = parser.parse_args([])
    assert hasattr(args, 'log_level')
    assert args.log_level == 'WARNING'  # Default log level
