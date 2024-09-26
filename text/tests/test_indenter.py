#!/usr/bin/env python3

import os
from io import StringIO

import pytest

import indenter
from indenter import detect_indent, apply_indent, process_indentation, parse_indent_code, format_indent_code

# Test data
SPACE_INDENTED = """
def hello():
    print("Hello, world!")
    if True:
        print("Nested block")
"""

TAB_INDENTED = """
def hello():
\tprint("Hello, world!")
\tif True:
\t\tprint("Nested block")
"""

MIXED_INDENTED = """
def hello():
    print("Hello, world!")
\tif True:
\t\tprint("Nested block")
"""

UNINDENTED = "def hello():\nprint('Hello, world!')\n"

COMMON_INDENTED = """
    def hello():
        print("Hello, world!")
        if True:
            print("Nested block")
"""

# Test detect_indent function
@pytest.mark.parametrize("input_text, expected", [
    (SPACE_INDENTED, (4, "s", 0)),
    (TAB_INDENTED, (1, "t", 0)),
    (MIXED_INDENTED, (1, "t", 0)),
    (UNINDENTED, (0, "", 0)),
    (COMMON_INDENTED, (4, "s", 1)),
])
def test_detect_indent(input_text, expected):
    assert detect_indent(input_text) == expected

# Test apply_indent function
@pytest.mark.parametrize("input_text, indent_size, indent_type, min_level, expected", [
    (SPACE_INDENTED, 1, "t", 0, TAB_INDENTED),
    (TAB_INDENTED, 4, "s", 0, SPACE_INDENTED),
    (UNINDENTED, 2, "s", 1, "  def hello():\n  print('Hello, world!')\n"),
    (COMMON_INDENTED, 2, "s", 0, SPACE_INDENTED.replace("    ", "  ")),
])
def test_apply_indent(input_text, indent_size, indent_type, min_level, expected):
    assert apply_indent(input_text, indent_size, indent_type, min_level).strip() == expected.strip()

# Test process_indentation function
def test_process_indentation_detect():
    input_stream = StringIO(SPACE_INDENTED)
    output_stream = StringIO()
    process_indentation(input_stream, output_stream, detect=True)
    assert output_stream.getvalue().strip() == "4s"

def test_process_indentation_apply():
    input_stream = StringIO(SPACE_INDENTED)
    output_stream = StringIO()
    process_indentation(input_stream, output_stream, apply="t")
    assert output_stream.getvalue().strip() == TAB_INDENTED.strip()

@pytest.mark.parametrize("input_text", [
    SPACE_INDENTED,
    TAB_INDENTED,
    UNINDENTED,
    COMMON_INDENTED,
])
def test_process_indentation_default(input_text):
    format = indenter.DEFAULT_INDENT
    input_stream = StringIO(input_text)
    output_stream = StringIO()
    expected = apply_indent(input_text, *parse_indent_code(format)).strip()
    process_indentation(input_stream, output_stream)
    assert output_stream.getvalue().strip() == expected

# Test edge cases
def test_empty_input():
    assert detect_indent("") == (0, "", 0)
    assert apply_indent("", 4, "s", 2) == "\n"

def test_single_line():
    assert detect_indent("print('Hello')") == (0, "", 0)
    assert apply_indent("print('Hello')", 2, "s", 1) == "  print('Hello')\n"

def test_mixed_indentation():
    mixed = "def foo():\n    print('bar')\n\tprint('baz')"
    assert detect_indent(mixed) == (4, "s", 0)
    assert apply_indent(mixed, 1, "t", 0) == "def foo():\n\tprint('bar')\nprint('baz')\n"

def test_large_indentation():
    large_indent = "def foo():\n        print('bar')"
    assert detect_indent(large_indent) == (8, "s", 0)
    assert apply_indent(large_indent, 2, "s", 1) == "  def foo():\n    print('bar')\n"

# Test invalid inputs
def test_invalid_indent_type():
    with pytest.raises(ValueError):
        parse_indent_code("x4")

def test_negative_min_level():
    with pytest.raises(ValueError):
        parse_indent_code("4s-1")

# Test parse_indent_code and format_indent_code
@pytest.mark.parametrize("indent_code, expected", [
    ("t", (1, "t", 0)),
    ("4s", (4, "s", 0)),
    ("2s1", (2, "s", 1)),
    ("t2", (1, "t", 2)),
])
def test_parse_indent_code(indent_code, expected):
    assert parse_indent_code(indent_code) == expected

@pytest.mark.parametrize("indent_size, indent_type, min_level, expected", [
    (1, "t", 0, "t"),
    (4, "s", 0, "4s"),
    (2, "s", 1, "2s1"),
    (1, "t", 2, "t2"),
])
def test_format_indent_code(indent_size, indent_type, min_level, expected):
    assert format_indent_code(indent_size, indent_type, min_level) == expected

# Test command-line interface
def test_cli_detect():
    input_stream = StringIO(SPACE_INDENTED)
    output_stream = StringIO()
    process_indentation(input_stream, output_stream, detect=True)
    assert output_stream.getvalue().strip() == "4s"

def test_cli_apply():
    input_stream = StringIO(SPACE_INDENTED)
    output_stream = StringIO()
    process_indentation(input_stream, output_stream, apply="t")
    assert output_stream.getvalue().strip() == TAB_INDENTED.strip()

def test_cli_default():
    input_stream = StringIO(UNINDENTED)
    output_stream = StringIO()
    process_indentation(input_stream, output_stream, apply="4s")
    expected_output = "def hello():\nprint('Hello, world!')\n"
    assert output_stream.getvalue().strip() == expected_output.strip()

if __name__ == "__main__":
    pytest.main([__file__])
