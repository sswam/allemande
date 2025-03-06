import os
import io
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Any

import chat as subject  # type: ignore

subject_name = subject.__name__

def test_safe_join_basic():
    base = Path("/tmp/test")
    assert subject.safe_join(base, "foo") == Path("/tmp/test/foo").resolve()
    assert subject.safe_join(base, "foo", "bar") == Path("/tmp/test/foo/bar").resolve()

def test_safe_join_parent_traversal():
    base = Path("/tmp/test")
    with pytest.raises(ValueError):
        subject.safe_join(base, "..")
    with pytest.raises(ValueError):
        subject.safe_join(base, "foo/../..")
    with pytest.raises(ValueError):
        subject.safe_join(base, "foo", "..", "..", "etc")

def test_safe_join_absolute():
    base = Path("/tmp/test")
    with pytest.raises(ValueError):
        subject.safe_join(base, "/etc/passwd")
    with pytest.raises(ValueError):
        subject.safe_join(base, "foo", "/etc/passwd")

def test_safe_join_error():
    base = Path("/home/sam/allemande/rooms")
    assert subject.safe_join(base, "cast/Soli.jpg") == Path("/home/sam/allemande/rooms/cast/Soli.jpg")

def test_sanitize_filename():
    # Basic sanitization
    assert subject.sanitize_filename("test.txt") == "test.txt"
    assert subject.sanitize_filename("test file.txt") == "test file.txt"

    # Remove leading/trailing dots and spaces
    assert subject.sanitize_filename(".test.txt") == "test.txt"
    assert subject.sanitize_filename("test.txt.") == "test.txt"
    assert subject.sanitize_filename(" test.txt ") == "test.txt"

    # Squeeze whitespace
    assert subject.sanitize_filename("test  file.txt") == "test file.txt"

    # Empty filename
    assert subject.sanitize_filename("") == ""
    assert subject.sanitize_filename(".") == ""
    assert subject.sanitize_filename(" ") == ""

def test_sanitize_pathname():
    # Basic paths
    assert subject.sanitize_pathname("foo/bar") == "foo/bar"
    assert subject.sanitize_pathname("foo/bar.txt") == "foo/bar.txt"

    # Remove empty parts
    assert subject.sanitize_pathname("foo//bar") == "foo/bar"
    assert subject.sanitize_pathname("/foo/bar/") == "foo/bar"

    # Squeeze whitespace
    assert subject.sanitize_pathname("foo\n\t bar") == "foo bar"

    # Too deep
    with pytest.raises(Exception):
        subject.sanitize_pathname("a/b/c/d/e/f/g/h/i/j/k")

    # Too long
    with pytest.raises(Exception):
        subject.sanitize_pathname("a" * 101)

    # Control characters
    with pytest.raises(Exception):
        subject.sanitize_pathname("foo\0bar")

def test_message_to_text():
    # Basic message
    msg = {"user": "Alice", "content": "Hello"}
    assert subject.message_to_text(msg) == "Alice:\tHello\n"

    # Multi-line message
    msg = {"user": "Alice", "content": "Hello\nWorld"}
    assert subject.message_to_text(msg) == "Alice:\tHello\n\tWorld\n"

    # Narrative (no user)
    msg = {"content": "Once upon a time"}
    assert subject.message_to_text(msg) == "Once upon a time\n"

def test_split_message_line():
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

def test_lines_to_messages():
    # Basic conversation
    lines = [
        "Alice:\tHello\n",
        "\tHow are you?\n",
        "Bob:\tI'm good\n",
        "Once upon a time\n"
    ]
    messages = list(subject.lines_to_messages(lines))
    assert len(messages) == 3
    assert messages[0] == {"user": "Alice", "content": "Hello\nHow are you?\n"}
    assert messages[1] == {"user": "Bob", "content": "I'm good\n"}
    assert messages[2] == {"content": "Once upon a time\n"}

def test_find_and_fix_inline_math():
    # Basic inline math
    text, has_math = subject.find_and_fix_inline_math("Let $x$ be a number")
    assert text == "Let $`x`$ be a number"
    assert has_math

    # No math
    text, has_math = subject.find_and_fix_inline_math("Just text")
    assert text == "Just text"
    assert not has_math

    # Code block should be preserved
    text, has_math = subject.find_and_fix_inline_math("Code `$x$` here")
    assert text == "Code `$x$` here"
    assert not has_math

def test_chat_message_dataclass():
    # Create message
    msg = subject.ChatMessage(user="Alice", content="Hello")
    assert msg.user == "Alice"
    assert msg.content == "Hello"

    # Narrative message
    msg = subject.ChatMessage(user=None, content="Once upon a time")
    assert msg.user is None
    assert msg.content == "Once upon a time"

def test_room_basic():
    rooms = os.environ['ALLEMANDE_ROOMS']
    room = subject.Room("test")
    assert room.name == "test"
    assert str(room.path) == f"{rooms}/test.bb"

def test_clean_prompt():
    # Basic cleanup
    prompt = ["Alice:", "\tHello Illu, please draw a cat"]
    cleaned = subject.clean_prompt(prompt, "Illu", " ")
    assert cleaned == "please draw a cat"

    # With code blocks
    prompt = ["Alice:", "\t```Illu, draw a cat```"]
    cleaned = subject.clean_prompt(prompt, "Illu", " ")
    assert cleaned == "draw a cat"


# This test file covers:
#
# 1. Safe path joining functionality with various edge cases
# 2. Filename and pathname sanitization
# 3. Message format conversion and parsing
# 4. Math expression handling
# 5. Basic Room functionality
# 6. Prompt cleaning functionality
#
# Key test features:
#
# - Tests for malicious path traversal attempts
# - Tests for empty/malformed inputs
# - Tests for edge cases like maximum path depth
# - Tests for control character handling
# - Tests for data format conversion
# - Tests for message continuation and narrative handling
#
# You may want to add more tests for:
#
# 1. Access control functionality
# 2. File backup functionality
# 3. Thinking section removal
# 4. Agent configuration handling
# 5. More complex Room operations
# 6. Exception handling for various error conditions
#
# Let me know if you'd like me to expand the test coverage in any particular area.
