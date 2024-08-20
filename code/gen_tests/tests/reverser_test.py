import textwrap
import pytest
from reverse_lines import reverse_lines


"""
Demo test for reverse_lines module.
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


def test_reverse_lines():
    """
    Test the reverse_lines function in the reverse_lines module.
    """
    input_lines = ql("""
        asdf
        qwer
    """)
    expected_response = ql("""
        fdsa
        rewq
    """)

    response = reverse_lines(input_lines)

    assert response == expected_response
