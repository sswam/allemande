import os

# disable DeprecationWarning https://github.com/jupyter/jupyter_core/issues/398
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"

import io
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import perfect as subject
subject_main = subject.perfect_py

def test_get_model_function():
    model_func = subject.get_model_function("op")
    assert callable(model_func)

def test_apply_improvement():
    old_content = "def foo():\n    pass"
    improvement = "def foo():\n    return 'improved'"
    assert subject.apply_improvement(old_content, improvement) == improvement

def test_detect_trivial_patch():
    assert subject.detect_trivial_patch("content", "content") == True
    assert subject.detect_trivial_patch("content", "new content") == False

def test_run_checks():
    assert subject.run_checks(Path("dummy.py")) == "Checks passed"

def test_run_tests():
    assert subject.run_tests(Path("dummy.py")) == "Tests passed"

@patch('llm.query')
@patch('perfect.open', new_callable=MagicMock)
@patch('perfect.Path')
def test_perfect_py(mock_path, mock_open, mock_query):
    mock_file = MagicMock()
    mock_file.read.return_value = "original content"
    mock_open.return_value.__enter__.return_value = mock_file
    mock_path.return_value.exists.return_value = True

    mock_query.return_value = "improved content"

    input_stream = io.StringIO("\n")  # Simulating user input if needed
    output_stream = io.StringIO()

    subject_main(file="test.py", istream=input_stream, ostream=output_stream)

    output = output_stream.getvalue()
    assert "File perfected" in output

@pytest.mark.parametrize("file_exists", [True, False])
def test_perfect_py_file_existence(file_exists):
    with patch('perfect.Path') as mock_path:
        mock_path.return_value.exists.return_value = file_exists

        if file_exists:
            with patch('perfect.open', new_callable=MagicMock):
                subject_main(file="test.py", istream=io.StringIO(), ostream=io.StringIO())
        else:
            with pytest.raises(FileNotFoundError):
                subject_main(file="test.py", istream=io.StringIO(), ostream=io.StringIO())

@patch('llm.query')
@patch('perfect.open', new_callable=MagicMock)
@patch('perfect.Path')
@patch('perfect.run_checks')
@patch('perfect.run_tests')
def test_perfect_py_with_failed_checks(mock_tests, mock_checks, mock_path, mock_open, mock_query):
    mock_file = MagicMock()
    mock_file.read.return_value = "original content"
    mock_open.return_value.__enter__.return_value = mock_file
    mock_path.return_value.exists.return_value = True

    mock_query.return_value = "improved content"
    mock_checks.return_value = "Checks failed"
    mock_tests.return_value = "Tests passed"

    input_stream = io.StringIO("User guidance\n")
    output_stream = io.StringIO()

    subject_main(file="test.py", istream=input_stream, ostream=output_stream)

    output = output_stream.getvalue()
    assert "Checks or tests failed" in output
    assert "Please provide guidance" in output

if __name__ == "__main__":
    pytest.main([__file__])

# Based on the provided `hello_py_test.py` and the `perfect.py` module, here's a corresponding `perfect_test.py` file:

# This test file follows the structure and conventions used in `hello_py_test.py`. It includes tests for the main functions in `perfect.py` and uses similar mocking techniques to test the `perfect_py` function. The tests cover various scenarios, including file existence checks, improvement application, and handling of failed checks or tests.

