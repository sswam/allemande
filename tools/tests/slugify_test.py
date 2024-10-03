import os

# disable DeprecationWarning https://github.com/jupyter/jupyter_core/issues/398
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"

import io
import pytest
from unittest.mock import patch

import slugify as subject
subject_main = subject.slugify

@pytest.mark.parametrize("input_text, expected_output", [
    ("Hello World", "Hello-World"),
    ("This is a test", "This-is-a-test"),
    ("123 & ABC", "123-and-ABC"),
    ("Test | Case", "Test-or-Case"),
    ("   Spaces   ", "Spaces"),
    ("!@#$%^&*()_+", "and"),
    ("", "-"),
])
def test_slugify_default(input_text, expected_output):
    result = subject_main(input_text)
    assert result == expected_output


@pytest.mark.parametrize("input_text, options, expected_output", [
    ("Hello World", {"hyphen": False}, "Hello_World"),
    ("This & That", {"boolean": False}, "This-That"),
    ("MiXeD CaSe", {"lower": True}, "mixed-case"),
    ("lower case", {"upper": True}, "LOWER-CASE"),
])
def test_slugify_options(input_text, options, expected_output):
    result = subject_main(input_text, **options)
    assert result == expected_output

def test_slugify_stream():
    input_stream = io.StringIO("Line 1\nLine 2 & 3\nTest | Case\n")
    output_stream = io.StringIO()

    subject_main(istream=input_stream, ostream=output_stream)

    output = output_stream.getvalue().splitlines()
    assert output == ["Line-1", "Line-2-and-3", "Test-or-Case"]

@pytest.mark.parametrize("input_lines, options, expected_output", [
    (["Hello", "World"], {"hyphen": False}, ["Hello", "World"]),
    (["Test & Case", "A | B"], {"boolean": False}, ["Test-Case", "A-B"]),
    (["MiXeD", "CaSe"], {"lower": True}, ["mixed", "case"]),
    (["lower", "case"], {"upper": True}, ["LOWER", "CASE"]),
])
def test_slugify_stream_options(input_lines, options, expected_output):
    input_stream = io.StringIO("\n".join(input_lines) + "\n")
    output_stream = io.StringIO()

    subject_main(istream=input_stream, ostream=output_stream, **options)

    output = output_stream.getvalue().splitlines()
    assert output == expected_output

def test_slugify_multiple_arguments():
    result = subject_main("Hello", "World", "Test")
    assert result == "Hello-World-Test"
