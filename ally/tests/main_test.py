import os

# disable DeprecationWarning https://github.com/jupyter/jupyter_core/issues/398
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"

import io
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

import main as subject

def test_get_module_name():
    assert subject.get_module_name() == 'main_test'
    assert subject.get_module_name(ext=True) == 'main_test.py'

def test_get_script_name():
    assert subject.get_script_name() == Path(sys.argv[0]).stem
    assert subject.get_script_name(ext=True) == Path(sys.argv[0]).name

def test_get_logger():
    logger = subject.get_logger()
    assert logger.name == 'main_test'

def test_get_log_level():
    with patch('main.get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_handler = MagicMock()
        mock_handler.level = 20
        mock_logger.handlers = [mock_handler]
        mock_get_logger.return_value = mock_logger

        assert subject.get_log_level() == 'INFO'

@patch('os.makedirs')
@patch('logging.FileHandler')
@patch('logging.StreamHandler')
@patch('os.chmod')
def test_setup_logging(mock_stream_handler, mock_file_handler, mock_makedirs):
    mock_logger = MagicMock()
    with patch('main.get_logger', return_value=mock_logger):
        subject.setup_logging('test_module', 'DEBUG')
    mock_makedirs.assert_called_once()
    mock_file_handler.assert_called_once()
    mock_stream_handler.assert_called_once()
    mock_logger.debug.assert_called_with("Starting test_module")
    mock_chmod.assert_called_once()

def test_CustomHelpFormatter():
    formatter = subject.CustomHelpFormatter('test')
    assert isinstance(formatter, subject.argparse.HelpFormatter)

def test_setup_logging_args():
    parser = subject.argparse.ArgumentParser()
    subject.setup_logging_args('test_module', parser)
    args = parser.parse_args([])
    assert hasattr(args, 'log_level')

def test_io():
    input_stream = io.StringIO("test input\n")
    output_stream = io.StringIO()
    get, put = subject.io(input_stream, output_stream)

    put("test output")
    assert output_stream.getvalue() == "test output\n"

    result = get()
    assert result == "test input"

def test_resource():
    with patch.dict('os.environ', {'ALLEMANDE_HOME': '/test/path'}):
        path = subject.resource('subdir/file.txt')
        assert str(path) == '/test/path/subdir/file.txt'

def test_IndentLogger():
    mock_logger = MagicMock()
    indent_logger = subject.IndentLogger(mock_logger)

    indent_logger.debug("Test message")
    mock_logger.debug.assert_called_with("Test message")

    indent_logger.indent(1)
    indent_logger.debug("Indented message")
    mock_logger.debug.assert_called_with("\tIndented message")

@patch('os.environ')
def test_find_in_path(mock_environ):
    mock_environ.__getitem__.return_value = '/bin:/usr/bin'
    with patch('pathlib.Path.is_file', return_value=True):
        assert subject.find_in_path('test_file') == '/usr/bin/test_file'

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

def test_upset():
    def outer():
        x = 0
        def inner():
            nonlocal x
            subject.upset('x', 1, level=1)
        inner()
        assert x == 1
    outer()

def test_is_binary():
    assert subject.is_binary('test.jpg') == True
    assert subject.is_binary('test.txt') == False
