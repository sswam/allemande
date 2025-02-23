import pytest
from typing import Any

import ally.re_map as subject

subject_name = subject.__name__

def test_empty_inputs():
    # Test empty text
    assert subject.apply_mappings("", {}, {}) == ""
    assert subject.apply_mappings("", {"pattern": "repl"}, {}) == ""
    assert subject.apply_mappings("", {}, {"pattern": "repl"}) == ""

    # Test empty mappings
    assert subject.apply_mappings("some text", {}, {}) == "some text"

def test_simple_replacements():
    # Basic single replacement
    assert subject.apply_mappings("hello", {"hello": "world"}, {}) == "world"

    # Multiple patterns
    mapping = {
        "cat": "dog",
        "black": "white"
    }
    assert subject.apply_mappings("black cat", mapping, {}) == "white dog"

def test_capture_groups():
    # Test basic capture group replacement
    mapping = {
        "(\\w+) world": "hello \\1"
    }
    assert subject.apply_mappings("goodbye world", mapping, {}) == "hello goodbye"

    # Test multiple capture groups
    mapping = {
        "(\\w+) (\\w+)": "\\2 \\1"
    }
    assert subject.apply_mappings("hello world", mapping, {}) == "world hello"

def test_priority_mappings():
    # Test that mapping_first takes precedence
    mapping = {
        "test": "regular"
    }
    mapping_first = {
        "test": "priority"
    }
    assert subject.apply_mappings("test", mapping, mapping_first) == "priority"

    # Test that subsequent matches use regular mapping
    text = "test test"
    assert subject.apply_mappings(text, mapping, mapping_first) == "priority regular"

def test_overlapping_patterns():
    mapping = {
        "ab": "X",
        "bc": "Y"
    }
    # Should match 'ab' first
    assert subject.apply_mappings("abc", mapping, {}) == "Xc"

def test_escaped_characters():
    # Test backslash handling
    mapping = {
        "test": "\\\\result"  # Double backslash to represent single backslash
    }
    assert subject.apply_mappings("test", mapping, {}) == "\\result"

def test_invalid_group_references():
    # Test reference to non-existent group
    mapping = {
        "(test)": "\\1 \\2"  # \\2 doesn't exist
    }
    assert subject.apply_mappings("test", mapping, {}) == "test \\2"

def test_complex_patterns():
    # Test more complex regex patterns
    mapping = {
        "\\b\\w+@\\w+\\.com\\b": "EMAIL",
        "\\b\\d{3}-\\d{3}-\\d{4}\\b": "PHONE"
    }
    text = "Contact: john@example.com or 123-456-7890"
    assert subject.apply_mappings(text, mapping, {}) == "Contact: EMAIL or PHONE"

def test_no_matches():
    # Test text that doesn't match any patterns
    mapping = {
        "pattern": "replacement"
    }
    assert subject.apply_mappings("no match here", mapping, {}) == "no match here"

def test_multiple_replacements_same_pattern():
    # Test multiple occurrences of the same pattern
    mapping = {
        "test": "CHECK"
    }
    assert subject.apply_mappings("test test test", mapping, {}) == "CHECK CHECK CHECK"

def test_case_sensitivity():
    # Test that matches are case-sensitive by default
    mapping = {
        "test": "CHECK"
    }
    assert subject.apply_mappings("TEST", mapping, {}) == "TEST"

def test_boundary_cases():
    # Test patterns at start and end of string
    mapping = {
        "^start": "BEGIN",
        "end$": "FINISH"
    }
    assert subject.apply_mappings("start middle end", mapping, {}) == "BEGIN middle FINISH"

# Here's a test file for `re_map.py`:

# This test file covers:
# - Empty input cases
# - Simple text replacements
# - Capture group handling
# - Priority mapping functionality
# - Overlapping patterns
# - Escaped character handling
# - Invalid group references
# - Complex regex patterns
# - Edge cases and boundary conditions
# - Multiple replacements
# - Case sensitivity
#
# The tests ensure that the `apply_mappings` function works correctly for various scenarios and edge cases that might occur in real-world usage.
