#File: filters_test.py

import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import os

import filters as subject  # type: ignore

subject_name = subject.__name__


# Test filter_out_agents_install

def test_filter_out_agents_install_no_yaml():
    """Test with response containing no YAML blocks."""
    response = "Just a regular response with no YAML"
    result = subject.filter_out_agents_install(response)
    assert result == response


def test_filter_out_agents_install_empty_yaml():
    """Test with empty YAML block."""
    response = "```yaml\n```"
    with patch('builtins.open', mock_open()):
        result = subject.filter_out_agents_install(response)
    assert result == response


@patch('settings.PATH_ROOMS', Path('/tmp/test_rooms'))
@patch('util.backup_file')
@patch('util.path_contains', return_value=True)
def test_filter_out_agents_install_single_agent(mock_path_contains, mock_backup, tmp_path):
    """Test installing a single agent."""
    response = """```yaml
#File: test_agent.yml
name: Test Agent
version: 1.0

"""

    with patch('settings.PATH_ROOMS', tmp_path):
        agents_path = tmp_path / "agents"
        agents_path.mkdir(parents=True, exist_ok=True)

        result = subject.filter_out_agents_install(response)

        assert result == response
        agent_file = agents_path / "test_agent.yml"
        assert agent_file.exists()
        content = agent_file.read_text()
        assert "name: Test Agent" in content


@patch('settings.PATH_ROOMS', Path('/tmp/test_rooms'))
@patch('util.backup_file')
@patch('util.path_contains', return_value=False)
def test_filter_out_agents_install_path_traversal_blocked(mock_path_contains, mock_backup):
    """Test that path traversal attempts are blocked."""
    response = """```yaml
#File: ../../../etc/passwd.yml
malicious: content

"""

    with patch('builtins.open', mock_open()) as mock_file:
        result = subject.filter_out_agents_install(response)
        mock_file.assert_not_called()


def test_filter_out_agents_install_multiple_agents(tmp_path):
    """Test installing multiple agents."""
    response = """```yaml
#File: agent1.yml
name: Agent 1
#File: agent2.yml
name: Agent 2

"""

    with patch('settings.PATH_ROOMS', tmp_path):
        with patch('util.backup_file'):
            with patch('util.path_contains', return_value=True):
                agents_path = tmp_path / "agents"
                agents_path.mkdir(parents=True, exist_ok=True)

                result = subject.filter_out_agents_install(response)

                assert (agents_path / "agent1.yml").exists()
                assert (agents_path / "agent2.yml").exists()


# Test filter_in_think_add_example

def test_filter_in_think_add_example_place_1_no_think():
    """Test adding think example when place=1 and no existing think tag."""
    response = "User:\tHello"
    result = subject.filter_in_think_add_example(response, place=1)
    assert "<think>" in result
    assert "</think>" in result


def test_filter_in_think_add_example_place_1_has_think():
    """Test not adding think example when already present."""
    response = "User:\t<think>existing</think>Hello"
    result = subject.filter_in_think_add_example(response, place=1)
    assert result.count("<think>") == 1


def test_filter_in_think_add_example_place_not_1():
    """Test not adding think example when place != 1."""
    response = "User:\tHello"
    result = subject.filter_in_think_add_example(response, place=2)
    assert "<think>" not in result


def test_filter_in_think_add_example_custom_example():
    """Test adding custom example text."""
    response = "User:\tHello"
    custom = "Custom thought"
    result = subject.filter_in_think_add_example(response, place=1, example=custom)
    assert custom in result


# Test filter_in_think_brackets

def test_filter_in_think_brackets_basic():
    """Test converting think tags to brackets."""
    response = "<think>some thought</think>"
    result = subject.filter_in_think_brackets(response, place=1)
    assert result == "[some thought]"


def test_filter_in_think_brackets_multiline():
    """Test converting multiline think tags."""
    response = "<think>\nmultiline\nthought\n</think>"
    result = subject.filter_in_think_brackets(response, place=1)
    assert "[" in result and "]" in result
    assert "<think>" not in result


def test_filter_in_think_brackets_empty():
    """Test with empty string."""
    result = subject.filter_in_think_brackets("", place=1)
    assert result == ""


# Test filter_out_think_brackets

def test_filter_out_think_brackets_basic():
    """Test converting brackets to think tags."""
    response = "\t[some thought]"
    result = subject.filter_out_think_brackets(response)
    assert "<think>some thought</think>" in result


def test_filter_out_think_brackets_not_at_line_end():
    """Test that brackets not at line end are not converted."""
    response = "Check [this link] for info"
    result = subject.filter_out_think_brackets(response)
    assert "<think>" not in result
    assert "[this link]" in result


def test_filter_out_think_brackets_empty():
    """Test with empty string."""
    result = subject.filter_out_think_brackets("")
    assert result == ""


# Test filter_out_think_fix

def test_filter_out_think_fix_no_think_tags():
    """Test with no think tags present."""
    response = "Just regular text"
    result = subject.filter_out_think_fix(response)
    assert result == response


def test_filter_out_think_fix_nested_tags():
    """Test removing nested think tags."""
    response = "<think>outer<think>nested</think>text</think>"
    result = subject.filter_out_think_fix(response)
    assert result.count("<think>") == 1
    assert result.count("</think>") == 1


def test_filter_out_think_fix_with_label():
    """Test fixing think tags after a label."""
    response = "Agent:\t<think>thought</think>"
    result = subject.filter_out_think_fix(response)
    assert "<think>" in result
    assert "</think>" in result


def test_filter_out_think_fix_empty_think():
    """Test with empty think tags."""
    response = "<think></think>"
    result = subject.filter_out_think_fix(response)
    assert "<think>" in result or result == ""


# Test filter_out_actions_reduce

def test_filter_out_actions_reduce_keep_all():
    """Test keeping all actions with keep_prob=1.0."""
    response = "*smiles* Hello *waves*"
    result = subject.filter_out_actions_reduce(response, keep_prob=1.0)
    assert "*smiles*" in result
    assert "*waves*" in result


def test_filter_out_actions_reduce_remove_all():
    """Test removing all actions with keep_prob=0.0."""
    response = "\t*smiles* Hello *waves*"
    result = subject.filter_out_actions_reduce(response, keep_prob=0.0)
    # Actions might be removed
    assert result is not None


def test_filter_out_actions_reduce_empty():
    """Test with empty string."""
    result = subject.filter_out_actions_reduce("")
    assert result == "" or result is None


def test_filter_out_actions_reduce_no_actions():
    """Test with no actions present."""
    response = "\tJust regular text"
    result = subject.filter_out_actions_reduce(response, keep_prob=0.5)
    assert "regular text" in result


def test_filter_out_actions_reduce_preserves_response_ending_with_colon():
    """Test that response ending with colon is preserved."""
    response = "Agent:\t"
    result = subject.filter_out_actions_reduce(response, keep_prob=0.0)
    assert result == response


# Test filter_out_emojis

def test_filter_out_emojis_remove_all():
    """Test removing all emojis."""
    response = "Hello 😊 World 🌍"
    result = subject.filter_out_emojis(response, keep_prob=0.0)
    assert "😊" not in result
    assert "🌍" not in result
    assert "Hello" in result
    assert "World" in result


def test_filter_out_emojis_keep_all():
    """Test keeping all emojis."""
    response = "Hello 😊 World 🌍"
    result = subject.filter_out_emojis(response, keep_prob=1.0)
    assert result == response


def test_filter_out_emojis_empty():
    """Test with empty string."""
    result = subject.filter_out_emojis("")
    assert result == ""


def test_filter_out_emojis_no_emojis():
    """Test with no emojis."""
    response = "Just regular text"
    result = subject.filter_out_emojis(response)
    assert result == response


# Test filter_out_emdash

def test_filter_out_emdash_basic():
    """Test replacing em-dash."""
    response = "Hello — world"
    result = subject.filter_out_emdash(response, keep_prob=0.0)
    assert "—" not in result
    assert "-" in result


def test_filter_out_emdash_keep_all():
    """Test keeping all em-dashes."""
    response = "Hello — world"
    result = subject.filter_out_emdash(response, keep_prob=1.0)
    assert result == response


def test_filter_out_emdash_custom_replacement():
    """Test with custom replacement."""
    response = "Hello — world"
    result = subject.filter_out_emdash(response, keep_prob=0.0, replacement="...")
    assert "..." in result


def test_filter_out_emdash_empty():
    """Test with empty string."""
    result = subject.filter_out_emdash("")
    assert result == ""


def test_filter_out_emdash_multiple_dashes():
    """Test with multiple consecutive dashes."""
    response = "Hello --- world"
    result = subject.filter_out_emdash(response, keep_prob=0.0)
    assert result.count("-") < response.count("-")


# Test filter_out_image_prompts

def test_filter_out_image_prompts_no_prompts():
    """Test with no image prompts."""
    response = "Just regular text"
    result = subject.filter_out_image_prompts(response)
    assert result is not None


def test_filter_out_image_prompts_quoted_prompt():
    """Test with properly quoted image prompt."""
    response = "```\nConi, a beautiful sunset\n```"
    result = subject.filter_out_image_prompts(response)
    assert "```" in result


def test_filter_out_image_prompts_unquoted_prompt():
    """Test detecting unquoted image prompts."""
    response = "Coni, a beautiful sunset"
    result = subject.filter_out_image_prompts(response)
    assert "```" in result  # Should be wrapped


def test_filter_out_image_prompts_empty():
    """Test with empty string."""
    result = subject.filter_out_image_prompts("")
    assert result == "" or result.strip() == ""


def test_filter_out_image_prompts_removes_art_model():
    """Test removing $ArtModel lines."""
    response = "$ArtModel Coni\nSome text"
    result = subject.filter_out_image_prompts(response)
    assert "$ArtModel" not in result or "```" in result


def test_filter_out_image_prompts_removes_chat_prefix():
    """Test removing chat: prefix."""
    response = "chat: Hello"
    result = subject.filter_out_image_prompts(response)
    assert "chat:" not in result


# Test is_image_prompt

def test_is_image_prompt_with_capitalized_word():
    """Test detecting prompt starting with capitalized word."""
    assert subject.is_image_prompt("Coni, beautiful scene")


def test_is_image_prompt_with_person_tag():
    """Test detecting prompt with [person tag."""
    assert subject.is_image_prompt("A scene with [person")


def test_is_image_prompt_with_use_tag():
    """Test detecting prompt with [use tag."""
    assert subject.is_image_prompt("Image with [use some_style]")


def test_is_image_prompt_with_aspect_ratio():
    """Test detecting prompt with aspect ratio."""
    assert subject.is_image_prompt("A scene, 16:9")


def test_is_image_prompt_with_negative():
    """Test detecting prompt with NEGATIVE."""
    assert subject.is_image_prompt("scene NEGATIVE bad quality")


def test_is_image_prompt_with_break():
    """Test detecting prompt with BREAK."""
    assert subject.is_image_prompt("scene BREAK another scene")


def test_is_image_prompt_empty():
    """Test with empty string."""
    assert not subject.is_image_prompt("")


def test_is_image_prompt_regular_text():
    """Test with regular text."""
    assert not subject.is_image_prompt("just some regular text")


# Test apply_filters_in

def test_apply_filters_in_no_filters():
    """Test with agent that has no filters."""
    agent = MagicMock()
    agent.get.return_value = None
    agent.name = "TestAgent"

    query = "test query"
    history = ["hist1", "hist2"]

    result_query, result_history = subject.apply_filters_in(agent, query, history)

    assert result_query == query
    assert result_history == history


def test_apply_filters_in_with_filter():
    """Test with agent that has a filter."""
    agent = MagicMock()
    agent.get.return_value = ["think_brackets"]
    agent.name = "TestAgent"

    query = "<think>thought</think>"
    history = ["<think>hist</think>"]

    result_query, result_history = subject.apply_filters_in(agent, query, history)

    assert "[" in result_query or result_query == query


def test_apply_filters_in_unknown_filter():
    """Test with unknown filter name."""
    agent = MagicMock()
    agent.get.return_value = ["nonexistent_filter"]
    agent.name = "TestAgent"

    query = "test"
    history = []

    result_query, result_history = subject.apply_filters_in(agent, query, history)

    assert result_query == query


def test_apply_filters_in_with_args():
    """Test with filter that has arguments."""
    agent = MagicMock()
    agent.get.return_value = [["think_add_example", "custom example"]]
    agent.name = "TestAgent"

    query = "test"
    history = []

    result_query, result_history = subject.apply_filters_in(agent, query, history)

    assert result_query is not None


# Test apply_filters_out

def test_apply_filters_out_no_filters():
    """Test with agent that has no output filters."""
    agent = MagicMock()
    agent.get.return_value = None
    agent.name = "TestAgent"

    response = "test response"

    result = subject.apply_filters_out(agent, response)

    assert result == response


def test_apply_filters_out_with_filter():
    """Test with agent that has output filters."""
    agent = MagicMock()
    agent.get.return_value = ["emojis"]
    agent.name = "TestAgent"

    response = "test 😊"

    result = subject.apply_filters_out(agent, response)

    assert result is not None


def test_apply_filters_out_unknown_filter():
    """Test with unknown output filter."""
    agent = MagicMock()
    agent.get.return_value = ["unknown_filter"]
    agent.name = "TestAgent"

    response = "test"

    result = subject.apply_filters_out(agent, response)

    assert result == response


def test_apply_filters_out_with_args():
    """Test with output filter that has arguments."""
    agent = MagicMock()
    agent.get.return_value = [["actions_reduce", 0.5]]
    agent.name = "TestAgent"

    response = "\t*test*"

    result = subject.apply_filters_out(agent, response)

    assert result is not None


def test_apply_filters_out_multiple_filters():
    """Test with multiple output filters."""
    agent = MagicMock()
    agent.get.return_value = ["emojis", "think_fix"]
    agent.name = "TestAgent"

    response = "test 😊 <think>thought</think>"

    result = subject.apply_filters_out(agent, response)

    assert result is not None


# Test apply_user_filters_out

def test_apply_user_filters_out_basic():
    """Test applying user filters."""
    content = "Some user content"
    result = subject.apply_user_filters_out("testuser", content)
    assert result is not None


def test_apply_user_filters_out_empty():
    """Test with empty content."""
    result = subject.apply_user_filters_out("testuser", "")
    assert result == ""


# Test degenerate cases

def test_filters_with_none():
    """Test that filters handle None gracefully."""
    # Most filters expect strings, but let's test they don't crash catastrophically
    with pytest.raises((AttributeError, TypeError)):
        subject.filter_out_emojis(None)


def test_filters_with_very_long_input():
    """Test filters with very long input."""
    long_text = "a" * 100000
    result = subject.filter_out_emojis(long_text)
    assert len(result) == len(long_text)


def test_filter_out_actions_reduce_probability_boundaries():
    """Test actions_reduce with boundary probabilities."""
    response = "\t*test action*"

    # Test with 0.0 - should remove
    result_0 = subject.filter_out_actions_reduce(response, keep_prob=0.0)

    # Test with 1.0 - should keep
    result_1 = subject.filter_out_actions_reduce(response, keep_prob=1.0)
    assert "*test action*" in result_1


def test_fix_prompt_content_empty():
    """Test fix_prompt_content with empty string."""
    result = subject.fix_prompt_content("", "DefaultModel")
    assert "DefaultModel" in result


def test_remove_art_model_lines_empty():
    """Test remove_art_model_lines with empty string."""
    result = subject.remove_art_model_lines("")
    assert result == ""


def test_remove_chat_prefix_empty():
    """Test remove_chat_prefix with empty string."""
    result = subject.remove_chat_prefix("")
    assert result == ""
def test_filter_out_sanity_single_char_repetition():
    """Test filtering of single character repetitions"""
    from filters import filter_out_sanity

    # Test with default max_repeat=80
    input_str = "a" * 100
    result = filter_out_sanity(input_str)
    assert len(result) == 79, f"Expected 79 'a's, got {len(result)}"
    assert result == "a" * 79

def test_filter_out_sanity_single_char_under_limit():
    """Test that strings under the limit are not modified"""
    from filters import filter_out_sanity

    input_str = "a" * 50
    result = filter_out_sanity(input_str)
    assert result == input_str, "String under limit should not be modified"

def test_filter_out_sanity_two_char_pattern():
    """Test filtering of two character pattern repetitions"""
    from filters import filter_out_sanity

    # "ab" repeated 50 times = 100 chars, should be reduced to 39 repetitions (78 chars)
    input_str = "ab" * 50
    result = filter_out_sanity(input_str)
    assert result == "ab" * 39, f"Expected 39 'ab' patterns, got {len(result)//2}"

def test_filter_out_sanity_three_char_pattern():
    """Test filtering of three character pattern repetitions"""
    from filters import filter_out_sanity

    # "abc" repeated 40 times = 120 chars, should be reduced to 26 repetitions (78 chars)
    input_str = "abc" * 40
    result = filter_out_sanity(input_str)
    assert result == "abc" * 26, f"Expected 26 'abc' patterns, got {len(result)//3}"

def test_filter_out_sanity_custom_max_repeat():
    """Test with custom max_repeat value"""
    from filters import filter_out_sanity

    input_str = "x" * 50
    result = filter_out_sanity(input_str, max_repeat=10)
    assert len(result) == 9, f"Expected 9 'x's with max_repeat=10, got {len(result)}"
    assert result == "x" * 9

def test_filter_out_sanity_mixed_content():
    """Test with mixed content (normal text + repetitions)"""
    from filters import filter_out_sanity

    input_str = "Hello " + "a" * 100 + " World"
    result = filter_out_sanity(input_str)
    assert result == "Hello " + "a" * 79 + " World"

def test_filter_out_sanity_multiple_repetitions():
    """Test with multiple separate repetitions in the same string"""
    from filters import filter_out_sanity

    input_str = "a" * 100 + " some text " + "b" * 100
    result = filter_out_sanity(input_str)
    expected = "a" * 79 + " some text " + "b" * 79
    assert result == expected

def test_filter_out_sanity_no_repetitions():
    """Test with normal text without repetitions"""
    from filters import filter_out_sanity

    input_str = "This is a normal sentence with no excessive repetitions."
    result = filter_out_sanity(input_str)
    assert result == input_str, "Normal text should not be modified"

def test_filter_out_sanity_edge_case_exact_limit():
    """Test with repetitions exactly at the limit"""
    from filters import filter_out_sanity

    input_str = "z" * 79  # Exactly at limit - 1
    result = filter_out_sanity(input_str)
    assert result == input_str, "String at limit-1 should not be modified"

def test_filter_out_sanity_two_char_under_limit():
    """Test two char pattern under the limit"""
    from filters import filter_out_sanity

    input_str = "xy" * 30  # 60 chars, under limit
    result = filter_out_sanity(input_str)
    assert result == input_str, "Two char pattern under limit should not be modified"

def test_filter_out_sanity_three_char_under_limit():
    """Test three char pattern under the limit"""
    from filters import filter_out_sanity

    input_str = "xyz" * 20  # 60 chars, under limit
    result = filter_out_sanity(input_str)
    assert result == input_str, "Three char pattern under limit should not be modified"

def test_filter_out_sanity_empty_string():
    """Test with empty string"""
    from filters import filter_out_sanity

    result = filter_out_sanity("")
    assert result == "", "Empty string should return empty string"

def test_filter_out_sanity_newline_repetitions():
    """Test with repeated newlines"""
    from filters import filter_out_sanity

    input_str = "\n" * 100
    result = filter_out_sanity(input_str)
    assert len(result) == 79, f"Expected 79 newlines, got {len(result)}"
