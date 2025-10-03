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
        'agent_names': ['alice', 'bob', 'charlie'],
        'chat_participants': ['alice', 'bob', 'charlie'],
        'chat_participants_all': ['alice', 'bob', 'charlie', 'dave'],
        'everyone_words': ['everyone', 'all'],
        'anyone_words': ['someone', 'anybody'],
        'self_words': ['me', 'myself'],
        'agent_name_map': {'alice': 'Alice', 'bob': 'Bob', 'charlie': 'Charlie'},
        'access_check_cache': {}
    }

def test_empty_content():
    result = subject.who_is_named("", "user", [])
    assert result == []

def test_no_agents():
    result = subject.who_is_named("Hello alice", "user", [])
    assert result == []

def test_simple_name_match():
    result = subject.who_is_named("Hello alice", "user", ["alice"])
    assert result == ["alice"]

def test_case_sensitivity():
    result = subject.who_is_named("Hello ALICE", "user", ["alice"], ignore_case=True)
    assert result == ["alice"]

    result = subject.who_is_named("Hello ALICE", "user", ["alice"], ignore_case=False)
    assert result == []

def test_self_words(basic_setup):
    setup = basic_setup
    result = subject.who_is_named(
        "me should do this",
        "alice",
        setup['agent_names'],
        self_words=setup['self_words']
    )
    assert result == ["alice"]

def test_everyone_words(basic_setup):
    setup = basic_setup
    result = subject.who_is_named(
        "everyone should see this",
        "alice",
        setup['agent_names'],
        chat_participants=setup['chat_participants'],
        everyone_words=setup['everyone_words']
    )
    assert sorted(result) == ["bob", "charlie"]

def test_anyone_words(basic_setup):
    setup = basic_setup
    with patch('random.choice', return_value='bob'):
        result = subject.who_is_named(
            "somebody should see this",
            "alice",
            setup['agent_names'],
            chat_participants=setup['chat_participants'],
            anyone_words=setup['anyone_words']
        )
        assert result == ["bob"]

def test_multiple_names_get_all(basic_setup):
    setup = basic_setup
    result = subject.who_is_named(
        "alice and bob should see this",
        "charlie",
        setup['agent_names'],
        get_all=True
    )
    assert sorted(result) == ["alice", "bob"]

def test_multiple_names_get_first(basic_setup):
    setup = basic_setup
    result = subject.who_is_named(
        "alice and bob should see this",
        "charlie",
        setup['agent_names'],
        get_all=False
    )
    assert len(result) == 1
    assert result[0] in ["alice", "bob"]

def test_access_control(mock_room, basic_setup):
    setup = basic_setup
    mock_room.check_access.return_value.value = 0  # No access

    result = subject.who_is_named(
        "alice should see this",
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

    assert subject.agent_is_tool(tool_agent) == True
    assert subject.agent_is_tool(image_agent) == True
    assert subject.agent_is_tool(normal_agent) == False

def test_filter_access(mock_room):
    access_cache = {}
    agent_map = {"alice": "Alice", "bob": "Bob"}

    result = subject.filter_access(
        ["@alice", "bob", "nonexistent"],
        mock_room,
        access_cache,
        agent_map
    )
    assert sorted(result) == ["Alice", "Bob"]

def test_name_patterns():
    patterns = [
        "alice, do this",
        "do this, alice",
        "alice do this",
        "do this alice",
        "`alice` do this"
    ]

    for pattern in patterns:
        result = subject.who_is_named(pattern, "user", ["alice"])
        assert result == ["alice"]

def test_uniq_flag():
    result = subject.who_is_named(
        "alice alice alice",
        "user",
        ["alice"],
        get_all=True,
        uniq=True
    )
    assert result == ["alice"]

    result = subject.who_is_named(
        "alice alice alice",
        "user",
        ["alice"],
        get_all=True,
        uniq=False
    )
    assert result == ["alice", "alice", "alice"]
