import pytest
from markdown_code import extract_code_from_markdown
import textwrap


""" tests for markdown_code.py """


def dedent_multiline_string(multiline_string: str) -> str:
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


qi = dedent_multiline_string


def test_extract_code_with_no_code():
    """
    Tests the function with a Markdown text that contains no code blocks.
    The expected output should consist of the original text turned into comments.
    """
    markdown = qi("""
        This is a test.
        Just some text.
    """)
    expected = qi("""
        # This is a test.
        # Just some text.
    """)
    assert extract_code_from_markdown(markdown, comment_prefix="#") == expected


def test_extract_code_with_single_code_block():
    """
    Tests the function with a single code block in Markdown.
    The expected output should keep the text outside the code block as comments and
    include the code block as-is in the output.
    """
    markdown = qi("""
        Here is some code:
        ```python
        print('Hello, world!')
        ```
    """)

    expected = qi("""
        # Here is some code:

        print('Hello, world!')
    """)

    assert extract_code_from_markdown(markdown, comment_prefix="#") == expected


def test_extract_code_with_multiple_code_blocks():
    """
    Tests the function with multiple code blocks in Markdown.
    The expected output should keep the text outside the code blocks as comments and
    include the code blocks as-is, separated by comments for the in-between text.
    """
    markdown = qi("""
        Here is some Python code:
        ```python
        print('Hello, world!')
        ```
        And here is some shell command:
        ```sh
        echo 'Hello, world!'
        ```
    """)
    expected = qi("""
        # Here is some Python code:

        print('Hello, world!')

        # And here is some shell command:

        echo 'Hello, world!'
    """)
    assert extract_code_from_markdown(markdown, comment_prefix="#") == expected


def test_extract_code_with_non_standard_comment_prefix():
    """
    Tests the function with a non-standard comment prefix.
    The expected output should use the provided comment prefix for the text outside
    the code block and include the code block as-is.
    """
    markdown = qi("""
        This is a test.
        ```python
        print('Hello, world!')
        ```
    """)
    expected = qi("""
        // This is a test.

        print('Hello, world!')
    """)
    assert extract_code_from_markdown(markdown, comment_prefix="//") == expected


def test_extract_code_with_no_comment_prefix():
    """
    Tests the function with the absence of a comment prefix.
    The expected output should exclude any text outside the code blocks,
    treating all text as part of the final code.
    """
    markdown = qi("""
        This is a test.
        ```python
        print('Hello, world!')
        ```
    """)
    expected = "print('Hello, world!')\n"
    assert extract_code_from_markdown(markdown, comment_prefix=None) == expected


def test_extract_code_with_empty_input():
    """
    Tests the function with completely empty Markdown text.
    The expected output should also be an empty string.
    """
    markdown = ""
    expected = ""
    assert extract_code_from_markdown(markdown, comment_prefix="#") == expected


def test_extract_code_with_only_code_blocks():
    """
    Tests the function with Markdown text that contains only code blocks.
    The expected output should include the code blocks as-is.
    """
    markdown = qi("""
        ```python
        print('Hello, world!')
        ```
        ```sh
        echo 'Hello, world!'
        ```
    """)
    expected = qi("""
        print('Hello, world!')

        echo 'Hello, world!'
    """)
    assert extract_code_from_markdown(markdown, comment_prefix="#") == expected


def test_extract_code_with_backticks_inside_code_block():
    """
    Tests the function with backticks inside the code block.
    The expected output should correctly capture and return the entire code block.
    """
    markdown = qi("""
        Here is some code with backticks:
        ```python
        print('This code has `backticks` inside.')
        ```
    """)
    expected = qi("""
        # Here is some code with backticks:

        print('This code has `backticks` inside.')
    """)
    assert extract_code_from_markdown(markdown, comment_prefix="#") == expected


def test_block_spacing():
    """
    Tests the spacing within and between blocks.
    """
    markdown = qi("""
        ```python
        print('Hello, world!')


        print('good stuff')
        ```

        hello world


        this is good
        ```sh
        echo 'Hello, world!'
        ```
    """)
    expected = qi("""
        print('Hello, world!')


        print('good stuff')

        # hello world
        #
        #
        # this is good

        echo 'Hello, world!'
    """)
    assert extract_code_from_markdown(markdown, comment_prefix="#") == expected
