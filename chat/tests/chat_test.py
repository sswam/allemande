"""Test module for chat functionality."""

from pathlib import Path
import re

import pytest
from bs4 import BeautifulSoup

import chat as subject  # type: ignore
from chat import apply_editing_commands
from chat import parse_markdown_attributes

subject_name = subject.__name__


def test_safe_join_basic():
    """Test basic path joining functionality."""
    base = Path("/tmp/test")
    assert subject.safe_join(base, "foo") == Path("/tmp/test/foo").resolve()
    assert subject.safe_join(base, "foo", "bar") == Path("/tmp/test/foo/bar").resolve()


def test_safe_join_parent_traversal():
    """Test that path traversal attacks are prevented."""
    base = Path("/tmp/test")
    with pytest.raises(ValueError, match="outside base directory"):
        subject.safe_join(base, "..")
    with pytest.raises(ValueError, match="outside base directory"):
        subject.safe_join(base, "foo/../..")
    with pytest.raises(ValueError, match="outside base directory"):
        subject.safe_join(base, "foo", "..", "..", "etc")


def test_safe_join_absolute():
    """Test handling of absolute paths."""
    base = Path("/tmp/test")
    with pytest.raises(ValueError, match="outside base directory"):
        subject.safe_join(base, "/etc/passwd")
    with pytest.raises(ValueError, match="outside base directory"):
        subject.safe_join(base, "foo", "/etc/passwd")


def test_safe_join_symlinks():
    """Test that symlinks are preserved but path traversal is still prevented."""
    base = Path("/home/sam/allemande/rooms")
    result = subject.safe_join(base, "cast/Soli.jpg")
    assert result == Path("/home/sam/allemande/rooms/cast/Soli.jpg")


def test_sanitize_filename():
    """Test filename sanitization rules."""
    # Basic sanitization
    assert subject.sanitize_filename("test.txt") == "test.txt"
    assert subject.sanitize_filename("test file.txt") == "test file.txt"
    assert subject.sanitize_filename("test..txt") == "test..txt"

    # Remove leading/trailing dots and spaces
    assert subject.sanitize_filename(".test.txt") == "test.txt"
    assert subject.sanitize_filename("test.txt.") == "test.txt"
    assert subject.sanitize_filename(" test.txt ") == "test.txt"

    # Squeeze whitespace
    assert subject.sanitize_filename("test  file.txt") == "test file.txt"
    assert subject.sanitize_filename("test\t \tfile.txt") == "test file.txt"

    # Empty filename
    assert subject.sanitize_filename("") == ""
    assert subject.sanitize_filename(".") == ""
    assert subject.sanitize_filename(" ") == ""


def test_sanitize_pathname():
    """Test pathname sanitization rules."""
    # Basic paths
    assert subject.sanitize_pathname("foo/bar") == "foo/bar"
    assert subject.sanitize_pathname("foo/bar.txt") == "foo/bar.txt"
    assert subject.sanitize_pathname("/foo/bar/") == "foo/bar/"

    # Remove empty parts and normalize slashes
    assert subject.sanitize_pathname("foo//bar") == "foo/bar"
    assert subject.sanitize_pathname("///foo///bar///") == "foo/bar/"

    # Squeeze whitespace
    assert subject.sanitize_pathname("foo  bar") == "foo bar"
    assert subject.sanitize_pathname("foo\n\t bar") == "foo bar"

    # Error cases
    with pytest.raises(Exception, match="too deeply nested"):
        subject.sanitize_pathname("a/b/c/d/e/f/g/h/i/j/k")

    with pytest.raises(Exception, match="too long"):
        subject.sanitize_pathname("a" * 1001)

    with pytest.raises(Exception, match="control characters"):
        subject.sanitize_pathname("foo\0bar")


def test_message_to_text():
    """Test conversion of message dict to text format."""
    # Basic message with user
    msg = {"user": "Alice", "content": "Hello"}
    assert subject.message_to_text(msg) == "Alice:\tHello\n"

    # Multi-line message
    msg = {"user": "Alice", "content": "Hello\nWorld"}
    assert subject.message_to_text(msg) == "Alice:\tHello\n\tWorld\n"

    # Narrative (no user)
    msg = {"content": "Once upon a time"}
    assert subject.message_to_text(msg) == "Once upon a time\n"

    # Empty content
    msg = {"user": "Alice", "content": ""}
    assert subject.message_to_text(msg) == "Alice:\t\n"


def test_split_message_line():
    """Test splitting message lines into user and content."""
    # Basic message
    user, content = subject.split_message_line("Alice:\tHello\n")
    assert user == "Alice"
    assert content == "Hello\n"

    # Narrative
    user, content = subject.split_message_line("Once upon a time\n")
    assert user == subject.USER_NARRATIVE
    assert content == "Once upon a time\n"

    # Continued line
    user, content = subject.split_message_line("\tAnd then...\n")
    assert user == subject.USER_CONTINUED
    assert content == "And then...\n"

    # Malformed line (missing colon)
    user, content = subject.split_message_line("Alice Hello\n")
    assert user == subject.USER_NARRATIVE
    assert content == "Alice Hello\n"


def test_lines_to_messages():
    """Test conversion of lines to message objects."""
    # Basic conversation
    lines = ["Alice:\tHello\n", "\tHow are you?\n", "Bob:\tI'm good\n", "Once upon a time\n"]
    messages = list(subject.lines_to_messages(lines))
    assert len(messages) == 3
    assert messages[0] == {"user": "Alice", "content": "Hello\nHow are you?\n"}
    assert messages[1] == {"user": "Bob", "content": "I'm good\n"}
    assert messages[2] == {"content": "Once upon a time\n"}


def test_find_and_fix_inline_math():
    """Test handling of inline math expressions."""
    # Basic inline math
    text, has_math = subject.find_and_fix_inline_math("Let $x$ be a number")
    assert text == "Let $`x`$ be a number"
    assert has_math

    # Multiple math expressions
    text, has_math = subject.find_and_fix_inline_math("$a$ + $b$ = $c$")
    assert text == "$`a`$ + $`b`$ = $`c`$"
    assert has_math

    # Code block should be preserved
    text, has_math = subject.find_and_fix_inline_math("Code `$x$` here")
    assert text == "Code `$x$` here"
    assert not has_math

    # Escaped math symbols
    text, has_math = subject.find_and_fix_inline_math("100% pure")
    assert text == "100% pure"
    assert not has_math


def test_find_and_fix_inline_math_part():
    """Test handling of inline math parts."""
    # Basic inline math
    part, has_math = subject.find_and_fix_inline_math_part("Let $x$ be")
    assert part == "Let $`x`$ be"
    assert has_math

    # Double dollar signs
    part, has_math = subject.find_and_fix_inline_math_part("$$x + y$$")
    assert part == "$`x + y`$"
    assert has_math

    # LaTeX brackets
    part, has_math = subject.find_and_fix_inline_math_part(r"\[x + y\]")
    assert has_math
    assert part == "$`x + y`$"

    # Escaped parentheses
    part, has_math = subject.find_and_fix_inline_math_part(r"\(x + y\)")
    assert has_math
    assert part == "$`x + y`$"


def test_preprocess_code_blocks():
    """Test preprocessing of indented code blocks."""
    content = """1.  HTML
    ```html
    <!DOCTYPE html>
    ```

    CSS
    ```css
    .hidden { display: none; }

    .invisible { visibility: hidden; }
    ```"""

    expect = """1.  HTML

    ```html
    <!DOCTYPE html>
    ```

    CSS

    ```css
    .hidden { display: none; }

    .invisible { visibility: hidden; }
    ```
"""

    result, has_math = subject.preprocess(content)
    assert not has_math
    assert result == expect


# TODO the following tests aren't very thorough ((

def test_preprocess_math_blocks():
    """Test preprocessing of math blocks."""
    content = """Here's some math:
    $$
    x = y^2
    $$
    And inline math $z = 1$"""

    result, has_math = subject.preprocess(content)
    assert has_math
    assert "```math" in result
    assert "$`z = 1`$" in result


def test_preprocess_script_tags():
    """Test preprocessing of script tags."""
    content = """<script>
    var x = 1;
    </script>
    Normal text"""

    result, has_math = subject.preprocess(content)
    assert not has_math
    assert "<script>" in result
    assert "var x = 1;" in result
    assert "Normal text" in result


def test_preprocess_svg():
    """Test preprocessing of SVG content."""
    content = """<svg>
    <rect x="0" y="0" width="100" height="100"/>
    </svg>"""

    result, has_math = subject.preprocess(content)
    assert not has_math
    assert "<svg>" in result
    assert "<rect" in result

# ))


def test_room_access():
    """Test room access control."""
    room = subject.Room("public")
    assert room.check_access("root") == subject.Access.ADMIN

    room = subject.Room("private/chat")
    assert room.check_access("guest").value & subject.Access.READ.value == 0


def test_clean_prompt():
    """Test cleaning of prompts for agents."""
    # Basic cleanup
    prompt = ["Alice:", "\tHello Illu, please draw a cat"]
    assert subject.clean_prompt(prompt, "Illu", " ") == "please draw a cat"

    # With code blocks
    prompt = ["Alice:", "\t```Illu, draw a cat```"]
    assert subject.clean_prompt(prompt, "Illu", " ") == "draw a cat"


def test_basic_message_no_meta():
    """Test messages with no meta tags pass through unchanged."""
    messages = [{"content": "Hello"}, {"content": "World"}]
    output = apply_editing_commands(messages)
    assert len(output) == 2
    assert output[0]["content"] == "Hello"
    assert output[1]["content"] == "World"


def test_remove_command():
    """Test removing a message."""
    messages = [{"content": "First"}, {"content": "Second"}, {"content": "Remove message 1 <allychat-meta remove='1'>"}]
    output = apply_editing_commands(messages)
    assert len(output) == 2
    assert output[0]["content"] == "First"
    assert output[1]["content"] == "Remove message 1"


def test_edit_command():
    """Test editing a message."""
    messages = [{"content": "Original"}, {"content": "Edit above <allychat-meta edit='0'>"}]
    output = apply_editing_commands(messages)
    assert len(output) == 1
    assert output[0]["content"] == "Edit above"


def test_insert_command():
    """Test inserting a message before another."""
    messages = [{"content": "First"}, {"content": "Insert before First <allychat-meta insert='0'>"}, {"content": "Last"}]
    output = apply_editing_commands(messages)
    assert len(output) == 3
    assert output[0]["content"] == "Insert before First"
    assert output[1]["content"] == "First"
    assert output[2]["content"] == "Last"


def test_empty_message_removal():
    """Test that empty messages after meta removal are marked for removal."""
    messages = [{"content": "Remove"}, {"content": "Keep"}, {"content": "<allychat-meta remove='0'>"}]
    output = apply_editing_commands(messages)
    assert len(output) == 1
    assert output[0]["content"] == "Keep"


def test_preserve_other_meta_attrs():
    """Test that non-editing meta attributes are preserved."""
    messages = [{"content": "Edit me"}, {"content": 'Test <allychat-meta edit="0" data-foo="bar">'}]
    output = apply_editing_commands(messages)
    assert len(output) == 1
    assert 'data-foo="bar"' in output[0]["content"]
    assert 'edit="0"' not in output[0]["content"]


def test_multiple_edits():
    """Test multiple edits on the same target message."""
    messages = [
        {"content": "Original"},
        {"content": "Edit 1 <allychat-meta edit='0'>"},
        {"content": "Edit 2 <allychat-meta edit='1'>"},
    ]
    output = apply_editing_commands(messages)
    assert len(output) == 1
    assert output[0]["content"] == "Edit 2"

def test_empty_attributes():
    assert parse_markdown_attributes("{}") == {}

def test_single_id():
    assert parse_markdown_attributes("{#myid}") == {"id": ["myid"]}

def test_single_class():
    assert parse_markdown_attributes("{.myclass}") == {"class": ["myclass"]}

def test_multiple_classes():
    assert parse_markdown_attributes("{.class1 .class2}") == {"class": ["class1", "class2"]}

def test_id_and_class():
    assert parse_markdown_attributes("{#myid .myclass}") == {"id": ["myid"], "class": ["myclass"]}

def test_simple_key_value():
    assert parse_markdown_attributes("{key=value}") == {"key": "value"}

def test_quoted_value():
    assert parse_markdown_attributes('{key="value with spaces"}') == {"key": "value with spaces"}

def test_single_quoted_value():
    assert parse_markdown_attributes("{key='value with spaces'}") == {"key": "value with spaces"}

def test_multiple_attributes():
    result = parse_markdown_attributes("{#myid .class1 key=value .class2}")
    assert result == {
        "id": ["myid"],
        "class": ["class1", "class2"],
        "key": "value"
    }

def test_boolean_attribute():
    assert parse_markdown_attributes("{disabled}") == {"disabled": True}

def test_complex_attributes():
    result = parse_markdown_attributes('{#main .big .bold title="Main Section" data-value=123 hidden}')
    assert result == {
        "id": ["main"],
        "class": ["big", "bold"],
        "title": "Main Section",
        "data-value": "123",
        "hidden": True
    }

def test_invalid_syntax():
    with pytest.raises(ValueError):
        parse_markdown_attributes("{invalid=}")

def test_mismatched_quotes():
    with pytest.raises(ValueError):
        parse_markdown_attributes('{key="unclosed string}')

def test_empty_key():
    with pytest.raises(ValueError):
        parse_markdown_attributes("{=value}")

def test_whitespace_handling():
    result = parse_markdown_attributes("{  #myid   .class1    key=value   }")
    assert result == {
        "id": ["myid"],
        "class": ["class1"],
        "key": "value"
    }

def test_special_characters():
    result = parse_markdown_attributes("{data-attr_123='value-123_456'}")
    assert result == {"data-attr_123": "value-123_456"}

def test_multiple_ids():
    result = parse_markdown_attributes("{#id1 #id2}")
    assert result == {"id": ["id1", "id2"]}

def test_mixed_quotes():
    result = parse_markdown_attributes('{key1="value1" key2=\'value2\'}')
    assert result == {"key1": "value1", "key2": "value2"}
