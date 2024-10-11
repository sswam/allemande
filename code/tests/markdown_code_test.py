import pytest
from markdown_code import extract_code_from_markdown
import textwrap

""" tests for markdown-code """

__version__ = "1.0.4"

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
    markdown = qi("""
        This is a test.
        Just some text.
    """)
    expected = qi("""
        # This is a test.
        # Just some text.
    """)
    assert extract_code_from_markdown(input_source=markdown, start_comment="#") == expected

def test_extract_code_with_single_code_block():
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
    assert extract_code_from_markdown(input_source=markdown, start_comment="#", first=False) == expected

def test_extract_code_with_multiple_code_blocks():
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
        print('Hello, world!')

        # Here is some Python code:

        # And here is some shell command:

        # echo 'Hello, world!'
    """)
    assert extract_code_from_markdown(input_source=markdown, start_comment="#") == expected

def test_extract_code_with_non_standard_start_comment():
    markdown = qi("""
        This is a test.
        ```python
        print('Hello, world!')
        ```
    """)
    expected = qi("""
        print('Hello, world!')

        // This is a test.
    """)
    assert extract_code_from_markdown(input_source=markdown, start_comment="//") == expected

def test_extract_code_with_no_start_comment():
    markdown = qi("""
        This is a test.
        ```python
        print('Hello, world!')
        ```
    """)
    expected = "print('Hello, world!')\n"
    assert extract_code_from_markdown(input_source=markdown, start_comment=None) == expected

def test_extract_code_with_empty_input():
    markdown = ""
    expected = ""
    assert extract_code_from_markdown(input_source=markdown, start_comment="#") == expected

def test_extract_code_with_only_code_blocks():
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

        # echo 'Hello, world!'
    """)
    assert extract_code_from_markdown(input_source=markdown, start_comment="#") == expected

def test_extract_code_with_backticks_inside_code_block():
    markdown = qi("""
        Here is some code with backticks:
        ```python
        print('This code has `backticks` inside.')
        ```
    """)
    expected = qi("""
        print('This code has `backticks` inside.')

        # Here is some code with backticks:
    """)
    assert extract_code_from_markdown(input_source=markdown, start_comment="#") == expected

def test_block_spacing():
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

        # echo 'Hello, world!'
    """)
    assert extract_code_from_markdown(input_source=markdown, start_comment="#") == expected

def test_shebang_fix():
    markdown = qi("""
        ```python
        #!/usr/bin/env python
        print('Hello, world!')
        ```
    """)
    expected = qi("""
        #!/usr/bin/env python

        print('Hello, world!')
    """)
    assert extract_code_from_markdown(input_source=markdown, start_comment="#", shebang_fix=True) == expected

def test_no_shebang_fix():
    markdown = qi("""
        ```python
        #!/usr/bin/env python
        print('Hello, world!')
        ```
    """)
    expected = qi("""
        #!/usr/bin/env python
        print('Hello, world!')
    """)
    assert extract_code_from_markdown(input_source=markdown, start_comment="#", shebang_fix=False) == expected

def test_strip_option():
    markdown = qi("""
        ```python
        print('Hello, world!')

        ```
    """)
    expected = "print('Hello, world!')\n"
    assert extract_code_from_markdown(input_source=markdown, start_comment="#", strip=True) == expected

def test_no_strip_option():
    markdown = qi("""
        ```python
        print('Hello, world!')

        ```
    """)
    expected = qi("""
        print('Hello, world!')

    """)
    assert extract_code_from_markdown(input_source=markdown, start_comment="#", strip=False) == expected

def test_first_option():
    markdown = qi("""
        ```python
        print('First block')
        ```
        Some text
        ```python
        print('Second block')
        ```
    """)
    expected = qi("""
    print('First block')
   
    # Some text
   
    # print('Second block')
    """)
    assert extract_code_from_markdown(input_source=markdown, start_comment="#", first=True) == expected

def test_no_first_option():
    markdown = qi("""
        ```python
        print('First block')
        ```
        Some text
        ```python
        print('Second block')
        ```
    """)
    expected = qi("""
        print('First block')

        # Some text

        # print('Second block')
    """)
    assert extract_code_from_markdown(input_source=markdown, start_comment="#", first=True) == expected

def test_select_specific_blocks():
    markdown = qi("""
        ```python
        print('First block')
        ```
        Some text
        ```python
        print('Second block')
        ```
        More text
        ```python
        print('Third block')
        ```
    """)
    expected = qi("""
        print('First block')

        # Some text

        # More text

        print('Third block')
    """)
    assert extract_code_from_markdown(input_source=markdown, start_comment="#", first=False, *[0, 2]) == expected
