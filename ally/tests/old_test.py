import os
import io
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import logging
import argparse

import ally.old as subject

subject_name = subject.__name__

__version__ = "0.1.4"

def test_TextInput():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write("test content")
        temp_file_path = temp_file.name

    try:
        text_input = subject.TextInput(temp_file_path)
        assert text_input.display == temp_file_path
        assert text_input.read() == "test content"
    finally:
        os.unlink(temp_file_path)


def test_load():
    mock_file_content = 'line 1\n# line 2\n\nline 3\n'
    expected_output = ['line 1', 'line 3']

    with patch('builtins.open', mock_open(read_data=mock_file_content)) as mock_file:
        result = subject.load('test_file')

    assert result == expected_output
    mock_file.assert_called_once_with(Path(os.environ["ALLEMANDE_HOME"])/'test_file', 'r', encoding='utf-8')
