#!/usr/bin/env python3

import os

# disable DeprecationWarning https://github.com/jupyter/jupyter_core/issues/398
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"

import io
import pytest
from unittest.mock import patch, MagicMock

import md_ol_ul as subject
subject_ol = subject.ol
subject_ul = subject.ul

@pytest.mark.parametrize("input_text, expected_output", [
    ("- Item 1\n- Item 2\n- Item 3\n", "1. Item 1\n2. Item 2\n3. Item 3\n"),
    ("  - Subitem\n- Item\n  - Another subitem\n", "  1. Subitem\n1. Item\n  2. Another subitem\n"),
    ("Regular text\n- List item\nMore text\n", "Regular text\n1. List item\nMore text\n"),
])
def test_ol(input_text, expected_output):
    input_stream = io.StringIO(input_text)
    output_stream = io.StringIO()

    subject_ol(istream=input_stream, ostream=output_stream)

    assert output_stream.getvalue() == expected_output

@pytest.mark.parametrize("input_text, expected_output", [
    ("1. Item 1\n2. Item 2\n3. Item 3\n", "- Item 1\n- Item 2\n- Item 3\n"),
    ("  1. Subitem\n1. Item\n  2. Another subitem\n", "  - Subitem\n- Item\n  - Another subitem\n"),
    ("Regular text\n1. List item\nMore text\n", "Regular text\n- List item\nMore text\n"),
])
def test_ul(input_text, expected_output):
    input_stream = io.StringIO(input_text)
    output_stream = io.StringIO()

    subject_ul(istream=input_stream, ostream=output_stream)

    assert output_stream.getvalue() == expected_output

def test_ol_mixed_input():
    input_text = "- Item 1\nRegular text\n- Item 2\n- Item 3\nMore text\n- Item 4\n"
    expected_output = "1. Item 1\nRegular text\n2. Item 2\n3. Item 3\nMore text\n1. Item 4\n"

    input_stream = io.StringIO(input_text)
    output_stream = io.StringIO()

    subject_ol(istream=input_stream, ostream=output_stream)

    assert output_stream.getvalue() == expected_output

def test_ul_mixed_input():
    input_text = "1. Item 1\nRegular text\n2. Item 2\n3. Item 3\nMore text\n1. Item 4\n"
    expected_output = "- Item 1\nRegular text\n- Item 2\n- Item 3\nMore text\n- Item 4\n"

    input_stream = io.StringIO(input_text)
    output_stream = io.StringIO()

    subject_ul(istream=input_stream, ostream=output_stream)

    assert output_stream.getvalue() == expected_output

@patch('sys.argv', ['md_ol.py'])
def test_main_ol():
    with patch('md_ol_ul.main.run') as mock_run:
        subject.__name__ = "__main__"
        exec(open('md_ol_ul.py').read())
        mock_run.assert_called_once_with(subject_ol)

@patch('sys.argv', ['md_ul.py'])
def test_main_ul():
    with patch('md_ol_ul.main.run') as mock_run:
        subject.__name__ = "__main__"
        exec(open('md_ol_ul.py').read())
        mock_run.assert_called_once_with(subject_ul)

@patch('sys.argv', ['invalid_name.py'])
def test_main_invalid_name():
    with patch('md_ol_ul.logger.error') as mock_error, \
        patch('sys.exit') as mock_exit:
        subject.__name__ = "__main__"
        exec(open('md_ol_ul.py').read())
        mock_error.assert_called_once_with("Invalid script name, should contain 'ul' or 'ol' but not both.")
        mock_exit.assert_called_once_with(1)

# Based on the provided information and the style of the test file for `hello_py.py`, here's a test file for `md_ol_ul.py`:

# This test file, `test_md_ol_ul.py`, follows the structure and style of the provided `test_hello_py.py`. It includes tests for both the `ol` and `ul` functions, as well as tests for mixed input and the main script execution logic. The tests use parametrized inputs to cover various scenarios and mock the necessary components to test the main script execution.

