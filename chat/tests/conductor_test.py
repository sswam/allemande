import pytest
from unittest.mock import patch, MagicMock
from typing import Any

import conductor as subject

subject_name = subject.__name__


def test_find_name_in_content():
    # Test start of line with comma
    assert subject.find_name_in_content("Alice, how are you?", "Alice")[0] == 0

    # Test end of line with comma
    assert subject.find_name_in_content("Hello, Alice", "Alice")[0] < 100

    # Test whole word matches
    assert subject.find_name_in_content("Hello Alice!", "Alice")[0] < 100

    # Test case insensitivity
    assert subject.find_name_in_content("hello ALICE", "Alice", ignore_case=True)[0] < 100

    # Test case sensitivity
    assert subject.find_name_in_content("hello ALICE", "Alice", ignore_case=False)[0] == 100

    # Test no match
    assert subject.find_name_in_content("Hello Bob", "Alice")[0] == 100

    # Test empty string
    assert subject.find_name_in_content("", "Alice")[0] == 100


def test_uniqo():
    # Test normal case
    assert subject.uniqo([1, 2, 2, 3, 3, 1]) == [1, 2, 3]

    # Test empty list
    assert subject.uniqo([]) == []

    # Test single element
    assert subject.uniqo([1]) == [1]

    # Test all duplicates
    assert subject.uniqo([1, 1, 1]) == [1]


def test_who_is_named():
    agents = ["Alice", "Bob", "Charlie"]
    content = "Hello Alice and Bob! How are you?"

    # Test basic name finding
    assert "Alice" in subject.who_is_named(content, "User", agents)

    # Test with empty content
    assert subject.who_is_named("", "User", agents) == []

    # Test with no agents
    assert subject.who_is_named(content, "User", []) == []

    # Test everyone words
    assert len(subject.who_is_named("Hey everyone!", "User", agents, chat_participants=agents, everyone_words=["everyone"])) == len(
        agents
    )

    # Test anyone words
    result = subject.who_is_named("Can anyone help?", "User", agents, chat_participants=agents, anyone_words=["anyone"])
    assert len(result) == 1
    assert result[0] in agents


def test_who_spoke_last():
    history = [{"user": "Alice", "content": "Hi"}, {"user": "Bob", "content": "Hello"}, {"user": "Charlie", "content": "Hey"}]
    agents = {"alice": {"type": "ai"}, "bob": {"type": "person"}, "charlie": {"type": "ai"}}

    # Test finding last AI speaker
    assert subject.who_spoke_last(history, "User", agents, include_humans=False) == ["Charlie"]

    # Test empty history
    assert subject.who_spoke_last([], "User", agents) == []

    # Test history with no valid speakers
    assert subject.who_spoke_last([{"content": "Hi"}], "User", agents) == []


def test_participants():
    history = [{"user": "Alice", "content": "Hi"}, {"user": "Bob", "content": "Hello"}, {"user": "System", "content": "Log"}]

    # Test normal case
    participants = subject.participants(history)
    assert "Alice" in participants
    assert "Bob" in participants
    assert "System" not in participants

    # Test empty history
    assert subject.participants([]) == []


def test_who_should_respond():
    agents = {
        "alice": {"name": "Alice", "type": "ai"},
        "bob": {"name": "Bob", "type": "person"},
        "tool": {"name": "Tool", "type": "tool"},
    }
    history = [{"user": "Alice", "content": "Hi"}, {"user": "Bob", "content": "Hello"}]
    message = {"user": "User", "content": "Hey Alice!"}

    # Test direct mention
    assert "Alice" in subject.who_should_respond(message, agents, history)

    # Test empty message
    empty_message = {"user": "User", "content": ""}
    assert len(subject.who_should_respond(empty_message, agents, history)) > 0

    # Test tool response
    tool_message = {"user": "Tool", "content": "Result"}
    result = subject.who_should_respond(tool_message, agents, history)
    assert len(result) > 0
    assert "Tool" not in result


def test_at_mention_all():
    agents = {
        "alice": {"name": "Alice", "type": "ai"},
        "bob": {"name": "Bob", "type": "ai"},
        "charlie": {"name": "Charlie", "type": "ai"},
    }
    history = [{"user": "Alice", "content": "Hi"}, {"user": "Bob", "content": "Hello"}]
    message = {"user": "User", "content": "@Alice and @Bob, what do you think?"}

    # Both @Alice and @Bob should be included in response
    result = subject.who_should_respond(message, agents, history)
    assert "Alice" in result
    assert "Bob" in result
    assert len(result) == 2


def test_at_mention_with_anyone():
    content = "Aetheria looks fully trippy, anyone know what to do next?"
    agents = ["@ally", "@barbie", "@callam", "@sam"]
    assert not subject.who_is_named(
        content,
        "User",
        agents,
        anyone_words=["@anyone", "@anybody", "@someone"],
        everyone_words=["@everyone", "@everybody"],
    )


# This test file includes tests for all the main functions in conductor.py, covering:
# - Basic functionality
# - Edge cases (empty inputs, single elements)
# - Different types of agents (AI, human, tool)
# - Name matching with different formats
# - Everyone/anyone words functionality
# - History parsing and participant tracking
