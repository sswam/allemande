"""Tests for unprompted_macros functionality."""

import pytest

import unprompted.unprompted_macros as subject

subject_name = subject.__name__


def test_unescape_string():
    """Test string unescaping functionality."""
    assert subject.unescape_string(r"hello\nworld") == "hello\nworld"
    assert subject.unescape_string(r"tab\there") == "tab\there"
    assert subject.unescape_string(r"\"quoted\"") == '"quoted"'
    assert subject.unescape_string(r"\'single\'") == "'single'"
    assert subject.unescape_string(r"\\backslash") == "\\backslash"
    assert subject.unescape_string("no escapes") == "no escapes"
    assert subject.unescape_string("") == ""
    assert subject.unescape_string("\\") == "\\"  # Single backslash


@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("[sets a=1]", ("sets", {"a": "1"}, 9)),
        ('[macro name="John Doe"]', ("macro", {"name": "John Doe"}, 22)),
        ('[test quoted="hello \\"world\\""]', ("test", {"quoted": 'hello "world"'}, 30)),
        ("[empty]", ("empty", {}, 6)),
    ],
)
def test_parse_macro_block(input_text, expected):
    """Test parsing of macro blocks with various formats."""
    name, pairs, end = subject.parse_macro_block(input_text, 0)
    assert name == expected[0]
    assert pairs == expected[1]
    assert end == expected[2]


def test_parse_macro_block_errors():
    """Test error cases for macro block parsing."""
    with pytest.raises(ValueError):
        subject.parse_macro_block("[]", 0)  # No name
    with pytest.raises(ValueError):
        subject.parse_macro_block("[unclosed", 0)  # No closing bracket
    with pytest.raises(ValueError):
        subject.parse_macro_block("[name", 0)  # No space after name


def test_parse_key_value_pairs():
    """Test parsing of key-value pairs."""
    assert not subject.parse_key_value_pairs("")
    assert subject.parse_key_value_pairs("a=1") == {"a": "1"}
    assert subject.parse_key_value_pairs("a=1 b=2") == {"a": "1", "b": "2"}
    assert subject.parse_key_value_pairs('x="hello world"') == {"x": "hello world"}
    assert subject.parse_key_value_pairs(r'path="C:\\dir"') == {"path": "C:\\dir"}


@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("", {}),
        ("No macros here", {}),
        ("[sets a=1]", {"sets": {"a": "1"}}),
        ("[sets a=1][sets b=2]", {"sets": {"a": "1", "b": "2"}}),
        ('[person name="John" age=30]', {"person": {"name": "John", "age": "30"}}),
        ('[config path="C:\\\\Program Files"]', {"config": {"path": "C:\\Program Files"}}),
        ("Invalid [macro", {}),  # Should handle invalid macros gracefully
    ],
)
def test_parse_macros(input_text, expected):
    """Test parsing of various macro formats."""
    assert subject.parse_macros(input_text) == expected


def test_parse_macros_nested_quotes():
    """Test parsing of macros with nested quotes."""
    input_text = r'[macro quote="say \"hello\""]'
    expected = {"macro": {"quote": 'say "hello"'}}
    assert subject.parse_macros(input_text) == expected


def test_parse_macros_multiple():
    """Test parsing of multiple macros in text."""
    input_text = """
    [config a=1 b=2]
    Some text here
    [person name="John" age=30]
    More text
    [config c=3]
    """
    expected = {"config": {"a": "1", "b": "2", "c": "3"}, "person": {"name": "John", "age": "30"}}
    assert subject.parse_macros(input_text) == expected


def test_parse_macros_edge_cases():
    """Test edge cases for macro parsing."""
    assert not subject.parse_macros("[]")
    assert not subject.parse_macros('[macro quote="unclosed]')
    text = r'[macro quote="\"quoted\" text"]'
    expected = {"macro": {"quote": '"quoted" text'}}
    assert subject.parse_macros(text) == expected


def test_parse_macros_performance():
    """Test macro parsing performance with large input."""
    large_text = "[macro a=1]\n" * 1000
    result = subject.parse_macros(large_text)
    assert len(result) == 1
    assert result["macro"] == {"a": "1"}


def test_update_macros():
    """Test updating macros with various scenarios."""
    # Update existing macro
    assert subject.update_macros("[sets width=100]", {"sets": {"width": "200"}}) == "[sets width=200]"

    # Add new setting to existing macro
    assert subject.update_macros("[sets width=100]", {"sets": {"height": "200"}}) == "[sets width=100 height=200]"

    # Add completely new macro
    assert subject.update_macros("", {"sets": {"width": "100"}}) == "[sets width=100]"

    # Update with spaces in value
    assert subject.update_macros("[config path=/tmp]", {"config": {"path": "Program Files"}}) == '[config path="Program Files"]'

    # Multiple updates
    result = subject.update_macros("[sets width=100]", {"sets": {"height": "200"}, "config": {"path": "/tmp"}})
    assert "[sets width=100 height=200]" in result
    assert "[config path=/tmp]" in result


def test_update_macros_with_prompt():
    """Test updating macros with prompt text."""
    # Test string prompt before macro
    assert subject.update_macros("[use Sia] beautiful girl", {"sets": {"width": "1024"}}) == "[use Sia] beautiful girl [sets width=1024]"

    # Test string prompt with existing macro
    assert subject.update_macros("[use Sia] beautiful girl [sets height=512]", {"sets": {"width": "1024"}}) == "[use Sia] beautiful girl [sets height=512 width=1024]"

    # Test multiple word prompt with new macro
    prompt = "a beautiful girl [use Sia] in a garden"
    assert subject.update_macros(prompt, {"sets": {"width": "1024"}}) == f"{prompt} [sets width=1024]"


def test_parse_and_update_macros():
    """Test parsing and updating macros in one step."""
    text = "a beautiful girl [use Sia] in a garden [sets width=100 height=200]"
    result = subject.parse_macros(text)
    assert result == {"sets": {"width": "100", "height": "200"}, "use": {"Sia": None}}
    result["sets"]["width"] = "1024"
    result["sets"]["height"] = "768"
    assert subject.update_macros(text, result) == "a beautiful girl [use Sia] in a garden [sets width=1024 height=768]"
    assert subject.update_macros("", result) == "[use Sia] [sets width=1024 height=768]"


def test_do_not_combine_macros():
    """Test that existing macros are not combined together."""
    text = "hello [use Sia] [use John] [use photo] world"
    result = subject.parse_macros(text)
    assert result == {"use": {"Sia": None, "John": None, "photo": None}}
    assert subject.update_macros(text, result) == "hello [use Sia] [use John] [use photo] world"


def test_delete_macro():
    """Test that we can delete a macro from text by setting its value to None."""
    text = "[L3] [foo a=1] hello [rp mode=attention] world"
    result = subject.parse_macros(text)
    # assert result == {"foo": {"a": "1"}, "rp": {"mode": "attention"}}
    result["L3"] = None
    result["rp"] = None
    assert subject.update_macros(text, result) == "[foo a=1] hello  world"
