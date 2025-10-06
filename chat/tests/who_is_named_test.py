import pytest
from unittest.mock import MagicMock, patch
from typing import Any

import who_is_named as subject

subject_name = subject.__name__

@pytest.fixture
def mock_room():
    room = MagicMock()
    room.check_access.return_value.value = 3  # READ_WRITE
    return room

@pytest.fixture
def basic_setup():
    return {
        'agent_names': ['Alice', 'Bob', 'Charlie'],
        'chat_participants': ['Alice', 'Bob', 'Charlie'],
        'chat_participants_all': ['Alice', 'Bob', 'Charlie', 'Dave'],
        'everyone_words': ['@everyone', '@all'],
        'anyone_words': ['@someone', '@anybody'],
        'self_words': ['@me', '@myself'],
        'agent_name_map': {'alice': 'Alice', 'bob': 'Bob', 'charlie': 'Charlie'},
        'access_check_cache': {}
    }

def test_empty_content():
    result = subject.who_is_named("", "user", [])
    assert result == []

def test_no_agents():
    result = subject.who_is_named("Hello Alice", "user", [])
    assert result == []

def test_simple_name_match():
    result = subject.who_is_named("Hello Alice", "user", ["Alice"])
    assert result == ["Alice"]

def test_case_sensitivity():
    result = subject.who_is_named("Hello ALICE", "user", ["Alice"], ignore_case=True)
    assert result == ["Alice"]

    result = subject.who_is_named("Hello ALICE", "user", ["Alice"], ignore_case=False)
    assert result == []

def test_self_words(basic_setup):
    setup = basic_setup
    result = subject.who_is_named(
        "@me should do this",
        "Alice",
        setup['agent_names'],
        chat_participants=setup['chat_participants'],
        self_words=setup['self_words'],
        everyone_words=setup['everyone_words'],
        anyone_words=setup['anyone_words'],
        agent_name_map=setup['agent_name_map']
    )
    assert result == ["Alice"]

def test_everyone_words(basic_setup):
    setup = basic_setup
    result = subject.who_is_named(
        "@everyone should see this",
        "Alice",
        setup['agent_names'],
        chat_participants=setup['chat_participants'],
        everyone_words=setup['everyone_words'],
        anyone_words=setup['anyone_words'],
        self_words=setup['self_words'],
        agent_name_map=setup['agent_name_map']
    )
    assert sorted(result) == ["Bob", "Charlie"]

def test_anyone_words(basic_setup):
    setup = basic_setup
    result = subject.who_is_named(
        "@someone should see this",
        "Alice",
        setup['agent_names'],
        chat_participants=setup['chat_participants'],
        everyone_words=setup['everyone_words'],
        anyone_words=setup['anyone_words'],
        self_words=setup['self_words'],
        agent_name_map=setup['agent_name_map']
    )
    assert len(result) == 1
    assert result[0] in ["Bob", "Charlie"]

def test_multiple_names_get_all(basic_setup):
    setup = basic_setup
    result = subject.who_is_named(
        "Alice and Bob should see this",
        "Charlie",
        setup['agent_names'],
        get_all=True
    )
    assert sorted(result) == ["Alice", "Bob"]

def test_multiple_names_get_first(basic_setup):
    setup = basic_setup
    result = subject.who_is_named(
        "Alice and Bob should see this",
        "Charlie",
        setup['agent_names'],
        get_all=False
    )
    assert len(result) == 1
    assert result[0] in ["Alice", "Bob"]

def test_access_control(mock_room, basic_setup):
    setup = basic_setup
    mock_room.check_access.return_value.value = 0  # No access

    result = subject.who_is_named(
        "Alice should see this",
        "user",
        setup['agent_names'],
        room=mock_room,
        access_check_cache=setup['access_check_cache'],
        agent_name_map=setup['agent_name_map']
    )
    assert result == []

def test_agent_is_tool():
    tool_agent = {"link": "tool", "type": "normal"}
    image_agent = {"link": "normal", "type": "image_gen"}
    normal_agent = {"link": "normal", "type": "normal"}

    assert subject.agent_is_tool(tool_agent) is True
    assert subject.agent_is_tool(image_agent) is True
    assert subject.agent_is_tool(normal_agent) is False

def test_filter_access(mock_room):
    access_cache = {}
    agent_map = {"alice": "Alice", "bob": "Bob"}

    result = subject.filter_access(
        ["@Alice", "Bob", "nonexistent"],
        mock_room,
        access_cache,
        agent_map
    )
    assert sorted(result) == ["Alice", "Bob"]

def test_name_patterns():
    patterns = [
        "Alice, do this",
        "do this, Alice",
        "Alice do this",
        "do this Alice",
        "`Alice` do this"
    ]

    for pattern in patterns:
        result = subject.who_is_named(pattern, "user", ["Alice"])
        assert result == ["Alice"]

def test_uniq_flag():
    result = subject.who_is_named(
        "Alice Alice Alice",
        "user",
        ["Alice"],
        get_all=True,
        uniq=True
    )
    assert result == ["Alice"]

    result = subject.who_is_named(
        "Alice Alice Alice",
        "user",
        ["Alice"],
        get_all=True,
        uniq=False
    )
    assert result == ["Alice", "Alice", "Alice"]

def test_extract_invocations_at_only():
    """Test extracting @-prefixed invocations only"""
    content = "Hey @Alice and @Bob, what about Charlie?"
    result = subject.extract_invocations(content, at_only=True)
    assert sorted(result) == ["Alice", "Bob"]

def test_extract_invocations_all():
    """Test extracting all name-like invocations"""
    content = "Hey @Alice and Bob_Smith, what about Charlie-Jones?"
    result = subject.extract_invocations(content, at_only=False)
    assert "Alice" in result
    assert "Bob_Smith" in result

def test_extract_unknown_invocations():
    """Test finding unknown agents/users"""
    content = "Hey @Alice, @Bob, and @NewAgent should see this"
    known_agents = ["Alice", "Bob"]
    result = subject.extract_unknown_invocations(
        content,
        agent_names=known_agents,
        at_only=True
    )
    assert result == ["NewAgent"]

def test_extract_unknown_invocations_with_users():
    """Test finding unknown agents excluding users"""
    content = "@Alice, @Bob, @Charlie, @NewAgent1, @NewAgent2"
    known_agents = ["Alice", "Bob"]
    known_users = ["Charlie"]
    result = subject.extract_unknown_invocations(
        content,
        agent_names=known_agents,
        all_users=known_users,
        at_only=True
    )
    assert sorted(result) == ["NewAgent1", "NewAgent2"]

def test_extract_unknown_invocations_case_insensitive():
    """Test case-insensitive matching for unknown detection"""
    content = "@Alice @BOB @NewAgent"
    known_agents = ["Alice", "Bob"]
    result = subject.extract_unknown_invocations(
        content,
        agent_names=known_agents,
        at_only=True,
        ignore_case=True
    )
    assert result == ["NewAgent"]

    # Case-sensitive should treat BOB as unknown (but not Alice which matches exactly)
    result = subject.extract_unknown_invocations(
        content,
        agent_names=known_agents,
        at_only=True,
        ignore_case=False
    )
    assert sorted(result) == ["BOB", "NewAgent"]
