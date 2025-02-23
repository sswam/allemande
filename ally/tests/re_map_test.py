import pytest
from typing import Any

import ally.re_map as subject

subject_name = subject.__name__


def test_empty_inputs():
    # Test empty text
    assert subject.apply_mappings(r"", {}, {}) == r""
    assert subject.apply_mappings(r"", {r"pattern": r"repl"}, {}) == r""
    assert subject.apply_mappings(r"", {}, {r"pattern": r"repl"}) == r""

    # Test empty mappings
    assert subject.apply_mappings(r"some text", {}, {}) == r"some text"


def test_simple_replacements():
    # Basic single replacement
    assert subject.apply_mappings(r"hello", {r"hello": r"world"}, {}) == r"world"

    # Multiple patterns
    mapping = {r"cat": r"dog", r"black": r"white"}
    assert subject.apply_mappings(r"black cat", mapping, {}) == r"white dog"


def test_capture_groups():
    # Test basic capture group replacement
    mapping = {r"(\w+) world": r"hello \1"}
    assert subject.apply_mappings(r"goodbye world", mapping, {}) == r"hello goodbye"

    # Test multiple capture groups
    mapping = {r"(\w+) (\w+)": r"\2 \1"}
    assert subject.apply_mappings(r"hello world", mapping, {}) == r"world hello"


def test_priority_mappings():
    # Test that mapping_first takes precedence
    mapping = {r"test": r"regular"}
    mapping_first = {r"test": r"priority"}
    assert subject.apply_mappings(r"test", mapping, mapping_first) == r"priority"

    # Test that subsequent matches use regular mapping
    text = r"test test"
    assert subject.apply_mappings(text, mapping, mapping_first) == r"priority regular"


def test_overlapping_patterns():
    mapping = {r"ab": r"X", r"bc": r"Y"}
    # Should match 'ab' first
    assert subject.apply_mappings(r"abc", mapping, {}) == r"Xc"


def test_escaped_characters():
    # Test backslash handling
    mapping = {r"test": r"\\result"}
    assert subject.apply_mappings(r"test", mapping, {}) == r"\result"


def test_invalid_group_references():
    # Test reference to non-existent group
    mapping = {r"(test)": r"\1 \2"}  # \\2 doesn't exist
    with pytest.raises(IndexError, match="no such group"):
        subject.apply_mappings(r"test", mapping, {})


def test_complex_patterns():
    # Test more complex regex patterns
    mapping = {r"\b\w+@\w+\.com\b": r"EMAIL", r"\b\d{3}-\d{3}-\d{4}\b": r"PHONE"}
    text = r"Contact: john@example.com or 123-456-7890"
    assert subject.apply_mappings(text, mapping, {}) == r"Contact: EMAIL or PHONE"


def test_no_matches():
    # Test text that doesn't match any patterns
    mapping = {r"pattern": r"replacement"}
    assert subject.apply_mappings(r"no match here", mapping, {}) == r"no match here"


def test_multiple_replacements_same_pattern():
    # Test multiple occurrences of the same pattern
    mapping = {r"test": r"CHECK"}
    assert subject.apply_mappings(r"test test test", mapping, {}) == r"CHECK CHECK CHECK"


def test_case_sensitivity():
    # Test that matches are case-sensitive by default
    mapping = {r"test": r"CHECK"}
    assert subject.apply_mappings(r"TEST", mapping, {}) == r"TEST"


def test_boundary_cases():
    # Test patterns at start and end of string
    mapping = {r"^start": r"BEGIN", r"end$": r"FINISH"}
    assert subject.apply_mappings(r"start middle end", mapping, {}) == r"BEGIN middle FINISH"


def test_complex_multiple_groups():
    # Multiple patterns with groups, mixing first and regular mappings
    mapping = {r"(\w+)\s+(\w+)": r"\2-\1", r"(\d+)-(\d+)": r"\2/\1"}  # Swaps words with hyphen  # Swaps numbers with slash
    mapping_first = {
        r"(\w+)\s+(\w+)": r"FIRST[\1-\2]",  # Should only apply once
        r"(\d+)-(\d+)": r"FIRST[\2::\1]",  # Should only apply once
    }

    # Test text with multiple matches for both patterns
    text = r"hello world 123-456 goodbye earth 789-012"
    result = subject.apply_mappings(text, mapping, mapping_first)
    assert result == r"FIRST[hello-world] FIRST[456::123] earth-goodbye 012/789"


def test_nested_groups():
    mapping = {r"((\w+)\s+(\w+))": r"\1[\2][\3]"}
    mapping_first = {r"((\w+)\s+(\w+))": r"FIRST(\1)(\2)(\3)"}

    text = r"alpha beta gamma delta"
    result = subject.apply_mappings(text, mapping, mapping_first)
    assert result == r"FIRST(alpha beta)(alpha)(beta) gamma delta[gamma][delta]"


def test_overlapping_groups():
    mapping = {r"(\w+)\s+(\w+)": r"\2-\1", r"(\w+)": r"X[\1]"}
    mapping_first = {r"(\w+)\s+(\w+)": r"FIRST[\1+\2]"}

    text = r"one two three four"
    result = subject.apply_mappings(text, mapping, mapping_first)
    assert result == r"FIRST[one+two] four-three"
