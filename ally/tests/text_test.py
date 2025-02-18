import os
import io
import pytest
from unittest.mock import patch, mock_open

from ally import text as subject

__version__ = "0.1.4"

subject_name = subject.__name__

def test_read_lines_single_file():
    mock_file_content = "Line 1\nLine 2\nLine 3"
    with patch('builtins.open', mock_open(read_data=mock_file_content)):
        result = subject.read_lines("test.txt")
        assert result == ["Line 1", "Line 2", "Line 3"]

def test_read_lines_multiple_files():
    mock_file_contents = ["File1 Line1\nFile1 Line2", "File2 Line1\nFile2 Line2"]
    with patch('builtins.open') as mock_open_func:
        mock_open_func.side_effect = [
            io.StringIO(content) for content in mock_file_contents
        ]
        result = subject.read_lines(["file1.txt", "file2.txt"])
        assert result == ["File1 Line1", "File1 Line2", "File2 Line1", "File2 Line2"]

def test_read_lines_strip_and_lower():
    mock_file_content = "  Line 1  \n  LINE 2  \n  Line 3  "
    with patch('builtins.open', mock_open(read_data=mock_file_content)):
        result = subject.read_lines("test.txt", strip=True, lower=True)
        assert result == ["line 1", "line 2", "line 3"]

def test_read_lines_file_not_found():
    with pytest.raises(FileNotFoundError):
        subject.read_lines("nonexistent_file.txt")

@pytest.mark.parametrize("input_text, expected_output", [
    ("This   is    a    test", "This is a test"),
    ("Multiple   spaces    between words", "Multiple spaces between words"),
    ("No extra spaces", "No extra spaces"),
    ("  Leading and trailing   spaces  ", " Leading and trailing spaces "),
    ("", "")
])
def test_squeeze(input_text, expected_output):
    assert subject.squeeze(input_text) == expected_output

@pytest.mark.parametrize("input_text, expected_output", [
    ("  Hello, World!  ", ("  ", "Hello, World!", "  ")),
    ("No leading or trailing spaces", ("", "No leading or trailing spaces", "")),
    ("\n\nMulti-line\ntext\n\n", ("\n\n", "Multi-line\ntext", "\n\n")),
    ("   ", ("   ", "", "")),
    ("", ("", "", ""))
])
def test_stripper(input_text, expected_output):
    assert subject.stripper(input_text) == expected_output
