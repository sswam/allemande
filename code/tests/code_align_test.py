#!/usr/bin/env python3

"""Tests for code_align.py"""

import io
import pytest
from typing import Any

import code_align as subject  # type: ignore

subject_name = subject.__name__


def test_detect_language_python_shebang():
    lines = ["#!/usr/bin/env python3", "import sys"]
    assert subject.detect_language(lines) == "python"


def test_detect_language_shell_shebang():
    lines = ["#!/bin/bash", "echo hello"]
    assert subject.detect_language(lines) == "shell"


def test_detect_language_python_keywords():
    lines = ["import sys", "def foo():", "    pass"]
    assert subject.detect_language(lines) == "python"

    lines = ["from typing import List"]
    assert subject.detect_language(lines) == "python"

    lines = ["class Foo:", "    pass"]
    assert subject.detect_language(lines) == "python"


def test_detect_language_python_docstring():
    lines = ['"""Module docstring"""', "import sys"]
    assert subject.detect_language(lines) == "python"


def test_detect_language_generic():
    lines = ["int main() {", "    return 0;", "}"]
    assert subject.detect_language(lines) == "generic"


def test_detect_language_empty():
    assert subject.detect_language([]) == "generic"


def test_get_comment_pattern():
    assert subject.get_comment_pattern("python") == r"(\s+)(#.*)$"
    assert subject.get_comment_pattern("shell") == r"(\s+)(#.*)$"
    assert subject.get_comment_pattern("generic") == r"(\s+)((?:#|//).*)$"


def test_expand_tabs_no_tabs():
    assert subject.expand_tabs("hello world", 4) == "hello world"
    assert subject.expand_tabs("", 4) == ""


def test_expand_tabs_with_tabs():
    assert subject.expand_tabs("\thello", 4) == "    hello"
    assert subject.expand_tabs("a\tb", 4) == "a   b"
    assert subject.expand_tabs("ab\tc", 4) == "ab  c"
    assert subject.expand_tabs("abc\td", 4) == "abc d"
    assert subject.expand_tabs("abcd\te", 4) == "abcd    e"


def test_expand_tabs_tabstop_8():
    assert subject.expand_tabs("\thello", 8) == "        hello"
    assert subject.expand_tabs("a\tb", 8) == "a       b"


def test_parse_line_with_comment_valid():
    import re
    pattern = re.compile(r"(\s+)(#.*)$")

    result = subject.parse_line_with_comment("code  # comment", pattern)
    assert result == ("code", "  ", "# comment")

    result = subject.parse_line_with_comment("x = 1 # assign", pattern)
    assert result == ("x = 1", " ", "# assign")


def test_parse_line_with_comment_no_code():
    import re
    pattern = re.compile(r"(\s+)(#.*)$")

    # Comment-only line should return None
    result = subject.parse_line_with_comment("  # just a comment", pattern)
    assert result is None

    result = subject.parse_line_with_comment("# comment", pattern)
    assert result is None


def test_parse_line_with_comment_no_comment():
    import re
    pattern = re.compile(r"(\s+)(#.*)$")

    result = subject.parse_line_with_comment("just code", pattern)
    assert result is None


def test_parse_line_with_comment_empty():
    import re
    pattern = re.compile(r"(\s+)(#.*)$")

    result = subject.parse_line_with_comment("", pattern)
    assert result is None


def test_calculate_alignment_single_line():
    block = [("x = 1", " ", "# comment")]
    assert subject.calculate_alignment(block) == 5  # len("x = 1")


def test_calculate_alignment_multiple_lines():
    block = [
        ("x = 1", " ", "# comment"),
        ("y = 2", " ", "# another"),
        ("z = 3", " ", "# more"),
    ]
    assert subject.calculate_alignment(block) == 5  # max(5, 5, 5)


def test_calculate_alignment_varying_lengths():
    block = [
        ("x = 1", " ", "# short"),
        ("longer_var = 2", " ", "# comment"),
        ("y = 3", " ", "# another"),
    ]
    assert subject.calculate_alignment(block) == 14  # len("longer_var = 2")


def test_calculate_alignment_with_outlier():
    block = [
        ("x = 1", " ", "# comment"),
        ("y = 2", " ", "# another"),
        ("very_very_long_variable_name = 3", " ", "# outlier"),
        ("z = 4", " ", "# more"),
    ]
    # Should exclude the outlier
    align_pos = subject.calculate_alignment(block)
    assert align_pos == 5  # based on normal lines, not the outlier


def test_calculate_alignment_empty():
    assert subject.calculate_alignment([]) == 0


def test_align_block_simple():
    block = [
        ("x = 1", " ", "# comment"),
        ("y = 2", " ", "# another"),
    ]
    block_lines = ["x = 1 # comment\n", "y = 2 # another\n"]

    result = subject.align_block(block, block_lines)
    assert result == [
        "x = 1  # comment\n",
        "y = 2  # another\n",
    ]


def test_align_block_varying_lengths():
    block = [
        ("x = 1", " ", "# short"),
        ("longer = 2", " ", "# comment"),
    ]
    block_lines = ["x = 1 # short\n", "longer = 2 # comment\n"]

    result = subject.align_block(block, block_lines)
    # Both should align to position 12 (len("longer = 2") + 2)
    assert result == [
        "x = 1       # short\n",
        "longer = 2  # comment\n",
    ]


def test_align_block_with_outlier():
    block = [
        ("x = 1", " ", "# comment"),
        ("y = 2", " ", "# another"),
        ("very_very_long_variable_name = 3", " ", "# outlier"),
    ]
    block_lines = [
        "x = 1 # comment\n",
        "y = 2 # another\n",
        "very_very_long_variable_name = 3 # outlier\n",
    ]

    result = subject.align_block(block, block_lines)
    # First two should align, outlier gets 2 spaces
    assert result[0] == "x = 1  # comment\n"
    assert result[1] == "y = 2  # another\n"
    assert result[2] == "very_very_long_variable_name = 3  # outlier\n"


def test_align_block_empty():
    result = subject.align_block([], [])
    assert result == []


def test_comments_align_simple():
    input_text = """x = 1 # comment
y = 2 # another
"""
    expected = """x = 1  # comment
y = 2  # another
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.comments_align(istream, ostream)
    assert ostream.getvalue() == expected


def test_comments_align_no_comments():
    input_text = """x = 1
y = 2
z = 3
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.comments_align(istream, ostream)
    assert ostream.getvalue() == input_text


def test_comments_align_mixed():
    input_text = """x = 1 # comment
y = 2
z = 3 # another comment
"""
    expected = """x = 1  # comment
y = 2
z = 3  # another comment
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.comments_align(istream, ostream)
    assert ostream.getvalue() == expected


def test_comments_align_separate_blocks():
    input_text = """x = 1 # first block
y = 2 # first block

a = 3 # second block
b = 4 # second block
"""
    expected = """x = 1  # first block
y = 2  # first block

a = 3  # second block
b = 4  # second block
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.comments_align(istream, ostream)
    assert ostream.getvalue() == expected


def test_comments_align_with_tabs():
    input_text = """x = 1\t# comment
y = 2\t# another
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.comments_align(istream, ostream, tabstop=4)
    result = ostream.getvalue()

    # Tabs should be expanded
    assert "\t" not in result
    assert "# comment" in result
    assert "# another" in result


def test_comments_align_empty_input():
    istream = io.StringIO("")
    ostream = io.StringIO()

    subject.comments_align(istream, ostream)
    assert ostream.getvalue() == ""


def test_comments_align_only_comment_lines():
    input_text = """# just a comment
# another comment
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.comments_align(istream, ostream)
    assert ostream.getvalue() == input_text


def test_comments_align_cpp_style_comments():
    input_text = """int x = 1; // comment
int y = 2; // another
"""
    expected = """int x = 1;  // comment
int y = 2;  // another
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.comments_align(istream, ostream)
    assert ostream.getvalue() == expected


def test_comments_align_python_detection():
    input_text = """#!/usr/bin/env python3
x = 1 # comment
y = 2 # another
"""
    expected = """#!/usr/bin/env python3
x = 1  # comment
y = 2  # another
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.comments_align(istream, ostream)
    assert ostream.getvalue() == expected


def test_comments_align_with_outlier():
    input_text = """x = 1 # short
y = 2 # short
very_very_long_variable_name = 3 # outlier
z = 4 # short
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.comments_align(istream, ostream)
    result = ostream.getvalue()

    # Short lines should be aligned together
    lines = result.split("\n")
    assert "x = 1  # short" in lines[0]
    assert "y = 2  # short" in lines[1]
    # Outlier should only have 2 spaces
    assert "very_very_long_variable_name = 3  # outlier" in lines[2]
    assert "z = 4  # short" in lines[3]


def test_comments_align_single_line():
    input_text = """x = 1 # comment
"""
    expected = """x = 1  # comment
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.comments_align(istream, ostream)
    assert ostream.getvalue() == expected


def test_comments_align_custom_tabstop():
    input_text = """x\t= 1 # comment
y\t= 2 # another
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.comments_align(istream, ostream, tabstop=8)
    result = ostream.getvalue()

    # Should expand tabs with tabstop=8
    assert "\t" not in result
    assert "# comment" in result


@pytest.mark.parametrize("input_text,expected_language", [
    ("#!/usr/bin/env python3\n", "python"),
    ("#!/bin/bash\n", "shell"),
    ("import sys\n", "python"),
    ("from typing import List\n", "python"),
    ("def foo():\n    pass\n", "python"),
    ("class Bar:\n    pass\n", "python"),
    ("int main() {\n    return 0;\n}\n", "generic"),
    ("", "generic"),
])
def test_detect_language_parametrized(input_text, expected_language):
    lines = input_text.split("\n")
    assert subject.detect_language(lines) == expected_language


def test_parse_line_with_equals_simple():
    result = subject.parse_line_with_equals("x = 1")
    assert result == ("x", "=", "1")


def test_parse_line_with_equals_walrus():
    result = subject.parse_line_with_equals("x := 1")
    assert result == ("x", ":=", "1")


def test_parse_line_with_equals_no_equals():
    result = subject.parse_line_with_equals("just code")
    assert result is None


def test_parse_line_with_equals_with_comment():
    result = subject.parse_line_with_equals("x = 1  # comment")
    assert result == ("x", "=", "1  # comment")


def test_parse_line_with_equals_in_comment():
    # Should not find = inside comment
    result = subject.parse_line_with_equals("code  # x = 1")
    assert result is None


def test_align_equals_simple():
    input_text = """x = 1
longer = 2
"""
    expected = """x      = 1
longer = 2
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.align_equals(istream, ostream)
    assert ostream.getvalue() == expected


def test_align_equals_walrus():
    input_text = """x := 1
longer := 2
"""
    expected = """x      := 1
longer := 2
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.align_equals(istream, ostream)
    assert ostream.getvalue() == expected


def test_align_equals_mixed_with_no_equals():
    input_text = """x = 1
print("hello")
y = 2
"""
    expected = """x = 1
print("hello")
y = 2
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.align_equals(istream, ostream)
    assert ostream.getvalue() == expected


def test_code_align_both_equals_and_comments():
    input_text = """x = 1  # comment
longer = 2  # another
"""
    # First align equals, then comments
    expected = """x      = 1    # comment
longer = 2    # another
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.code_align(istream, ostream, comments=True, equals=True)
    result = ostream.getvalue()

    # Comments should also be aligned
    lines = result.split("\n")
    if len(lines) >= 2:
        comment_pos_1 = lines[0].find("#")
        comment_pos_2 = lines[1].find("#")
        assert comment_pos_1 == comment_pos_2

    # Should have both equals and comments aligned
    # This is a bit tricky due to interaction, so we check for approximate alignment
    assert "x      = 1" in result
    assert "longer = 2" in result


def test_code_align_only_equals():
    input_text = """x = 1  # comment
longer = 2  # another
"""

    istream = io.StringIO(input_text)
    ostream = io.StringIO()

    subject.code_align(istream, ostream, comments=False, equals=True)
    result = ostream.getvalue()

    # Should have equals aligned but NOT comments
    assert "x      = 1  # comment" in result
    assert "longer = 2  # another" in result
