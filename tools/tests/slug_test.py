import os

# disable DeprecationWarning https://github.com/jupyter/jupyter_core/issues/398
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"

import pytest
from ally.geput import make_get_put

import slug as subject
subject_main = subject.slug

@pytest.mark.parametrize("input_text, expected_output", [
    ("Hello World", "Hello-World"),
    ("This is a test", "This-is-a-test"),
    ("123 & ABC", "123-and-ABC"),
    ("Test | Case", "Test-or-Case"),
    ("   Spaces   ", "Spaces"),
    ("!@#$%^&*()_+", "and"),
    ("", "-"),
])
def test_default(input_text, expected_output):
    result = subject_main(text=input_text)
    assert result == expected_output

@pytest.mark.parametrize("input_text, options, expected_output", [
    ("Hello World", {"underscore": True}, "Hello_World"),
    ("This & That", {"boolean": False}, "This-That"),
    ("MiXeD CaSe", {"lower": True}, "mixed-case"),
    ("lower case", {"upper": True}, "LOWER-CASE"),
])
def test_options(input_text, options, expected_output):
    result = subject_main(text=input_text, **options)
    assert result == expected_output

def test_stream():
    input_lines = ["Line 1", "Line 2 & 3", "Test | Case"]
    output = []
    get, put = make_get_put(input_lines, output)

    subject_main(get=get, put=put)
    assert output == ["Line-1", "Line-2-and-3", "Test-or-Case"]

@pytest.mark.parametrize("input_lines, options, expected_output", [
    (["Hello", "World"], {"underscore": True}, ["Hello", "World"]),
    (["Test & Case", "A | B"], {"boolean": False}, ["Test-Case", "A-B"]),
    (["MiXeD", "CaSe"], {"lower": True}, ["mixed", "case"]),
    (["lower", "case"], {"upper": True}, ["LOWER", "CASE"]),
])
def test_stream_options(input_lines, options, expected_output):
    output = []
    get, put = make_get_put(input_lines, output)

    subject_main(get=get, put=put, **options)
    assert output == expected_output

def test_multiple_arguments():
    result = subject_main(text="Hello World")
    assert result == "Hello-World"
