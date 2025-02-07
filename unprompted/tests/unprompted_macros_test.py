import pytest
from typing import Any

import unprompted.unprompted_macros as subject

subject_name = subject.__name__

def test_unescape_string():
    assert subject.unescape_string(r'hello\nworld') == 'hello\nworld'
    assert subject.unescape_string(r'tab\there') == 'tab\there'
    assert subject.unescape_string(r'\"quoted\"') == '"quoted"'
    assert subject.unescape_string(r"\'single\'") == "'single'"
    assert subject.unescape_string(r'\\backslash') == '\\backslash'
    assert subject.unescape_string('no escapes') == 'no escapes'
    assert subject.unescape_string('') == ''
    assert subject.unescape_string('\\') == '\\'  # Single backslash

@pytest.mark.parametrize("input_text, expected", [
    ("[sets a=1]", ("sets", {"a": "1"}, 9)),
    ('[macro name="John Doe"]', ("macro", {"name": "John Doe"}, 22)),
    ('[test quoted="hello \\"world\\""]', ("test", {"quoted": 'hello "world"'}, 30)),
    ('[empty]', ("empty", {}, 6)),
])
def test_parse_macro_block(input_text, expected):
    name, pairs, end = subject.parse_macro_block(input_text, 0)
    assert name == expected[0]
    assert pairs == expected[1]
    assert end == expected[2]

def test_parse_macro_block_errors():
    with pytest.raises(ValueError):
        subject.parse_macro_block("[]", 0)  # No name
    with pytest.raises(ValueError):
        subject.parse_macro_block("[unclosed", 0)  # No closing bracket
    with pytest.raises(ValueError):
        subject.parse_macro_block("[name", 0)  # No space after name

def test_parse_key_value_pairs():
    assert subject.parse_key_value_pairs('') == {}
    assert subject.parse_key_value_pairs('a=1') == {'a': '1'}
    assert subject.parse_key_value_pairs('a=1 b=2') == {'a': '1', 'b': '2'}
    assert subject.parse_key_value_pairs('x="hello world"') == {'x': 'hello world'}
    assert subject.parse_key_value_pairs(r'path="C:\\dir"') == {'path': 'C:\\dir'}

@pytest.mark.parametrize("input_text, expected", [
    ("", {}),
    ("No macros here", {}),
    ("[sets a=1]", {"sets": {"a": "1"}}),
    ("[sets a=1][sets b=2]", {"sets": {"a": "1", "b": "2"}}),
    ('[person name="John" age=30]', {"person": {"name": "John", "age": "30"}}),
    ('[config path="C:\\\\Program Files"]', {"config": {"path": "C:\\Program Files"}}),
    ('Invalid [macro', {}),  # Should handle invalid macros gracefully
])
def test_parse_macros(input_text, expected):
    assert subject.parse_macros(input_text) == expected

def test_parse_macros_nested_quotes():
    input_text = r'[macro quote="say \"hello\""]'
    expected = {"macro": {"quote": 'say "hello"'}}
    assert subject.parse_macros(input_text) == expected

def test_parse_macros_multiple():
    input_text = """
    [config a=1 b=2]
    Some text here
    [person name="John" age=30]
    More text
    [config c=3]
    """
    expected = {
        "config": {"a": "1", "b": "2", "c": "3"},
        "person": {"name": "John", "age": "30"}
    }
    assert subject.parse_macros(input_text) == expected

def test_parse_macros_edge_cases():
    # Test empty brackets
    assert subject.parse_macros("[]") == {}

    # Test unclosed quotes
    assert subject.parse_macros('[macro quote="unclosed]') == {}

    # Test multiple escaped quotes
    text = r'[macro quote="\"quoted\" text"]'
    expected = {"macro": {"quote": '"quoted" text'}}
    assert subject.parse_macros(text) == expected

def test_parse_macros_performance():
    # Test with a large number of macros
    large_text = "[macro a=1]\n" * 1000
    result = subject.parse_macros(large_text)
    assert len(result) == 1
    assert result["macro"] == {"a": "1"}

def test_main():
    # Test that the main test function runs without errors
    subject.test()

# Here's a test file for `unprompted_macros.py`:

# This test file includes:
#
# 1. Tests for string unescaping with various escape sequences
# 2. Parameterized tests for macro block parsing
# 3. Error case testing for invalid macro formats
# 4. Tests for key-value pair parsing
# 5. Comprehensive tests for the main parse_macros function
# 6. Edge case testing with empty inputs, invalid formats
# 7. Performance test with large input
# 8. Tests for nested quotes and escape sequences
# 9. Test for the main test function
#
# The tests cover:
# - Empty inputs
# - Invalid formats
# - Nested quotes
# - Escape sequences
# - Multiple macros
# - Macro merging
# - Large inputs
# - Edge cases that might break the parser
