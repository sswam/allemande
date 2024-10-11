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

import ally.filer as subject

__version__ = "0.1.4"


def test_resource():
    with patch.dict('os.environ', {'ALLEMANDE_HOME': '/test/path'}):
        path = subject.resource('subdir/file.txt')
        assert str(path) == '/test/path/subdir/file.txt'


@patch('pathlib.Path.is_file', return_value=True)
def test_find_in_path(mock_is_file):
    with patch.dict('os.environ', {'PATH': '/fakebin:/usr/fakebin'}):
        assert subject.find_in_path('test_file') == '/fakebin/test_file'


def test_is_binary():
    assert subject.is_binary('test.jpg') == True
    assert subject.is_binary('test.txt') == False
