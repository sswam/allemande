import textwrap
import pytest
from hello import hello


"""
Demo test including dedent.
"""


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
    output = quote(multiline_string).split("\n")
    if output and output[-1] == "":
        output.pop()
    return output


qi = quote
ql = quote_list


def test_hello_with_name_and_reverse():
    """
    Test the hello function in the hello module with a specific name and reverse flag.
    """
    input_lines = ql("""
        How are you today?
        Nice to meet you.
    """)
    expected_response = ql("""
        Nice to meet you.
        How are you today?
        Hello, Sam
    """)

    response = hello(input_lines, name="Sam", reverse=True)

    assert response == expected_response
