import io
import textwrap
import pytest
import subprocess
import sys

from hello import hello, __version__

def quote(multiline_string):
    """
    Remove any common leading whitespace from every line in the input string.

    Args:
        multiline_string (str): The input string containing multiple lines.

    Returns:
        str: The dedented string with common leading whitespace removed.
    """
    s = textwrap.dedent(multiline_string)
    if s.startswith("\n"):
        return s[1:]
    return s


def quote_list(multiline_string):
    """
    Convert a multiline string into a list of lines with common leading whitespace removed.

    Args:
        multiline_string (str): The input string containing multiple lines.

    Returns:
        list: A list of lines with common leading whitespace removed.
    """
    return quote(multiline_string).splitlines()

qi = quote
ql = quote_list

@pytest.mark.parametrize("input_lines, name, reverse, expected", [
    (["Line 1", "Line 2"], "World", False, ["Hello, World", "Line 1", "Line 2"]),
    (["Line 1", "Line 2"], "Sam", True, ["Line 2", "Line 1", "Hello, Sam"]),
    ([], "Alice", False, ["Hello, Alice"]),
    (["Single line"], "Bob", True, ["Single line", "Hello, Bob"]),
])
def test_hello(input_lines, name, reverse, expected):
    assert hello(input_lines, name=name, reverse=reverse) == expected

def test_hello_with_multiline_input():
    input_lines = ql("""
        How are you today?
        Nice to meet you.
        Have a great day!
    """)
    expected_response = ql("""
        Have a great day!
        Nice to meet you.
        How are you today?
        Hello, Sam
    """)

    response = hello(input_lines, name="Sam", reverse=True)
    assert response == expected_response

@pytest.fixture
def mock_input(monkeypatch):
    def mock_stdin(text):
        monkeypatch.setattr('sys.stdin', text)
    return mock_stdin

def test_main_cli(monkeypatch, capsys):
    input_text = io.StringIO(qi("""
        Line 1
        Line 2
    """))
    monkeypatch.setattr('sys.stdin', input_text)
    monkeypatch.setattr('sys.argv', ['hello.py', '--name', 'Alice', '--reverse'])

    from hello import main
    main(name="Alice", reverse=True)

    captured = capsys.readouterr()
    print(repr(captured))
    expected_output = qi("""
        Line 2
        Line 1
        Hello, Alice
    """)
    assert captured.out == expected_output

def test_version():
    assert __version__ == "1.0.0"

def test_cli_error_handling():
    result = subprocess.run(['python', 'hello.py', '--invalid-arg'], 
                            capture_output=True, text=True)
    assert result.returncode != 0
    assert "error:" in result.stderr.lower()
