#!/usr/bin/env python3

"""Test llm.py."""

import pytest
import llm


def test_replace_citations_basic():
    """Test basic citation replacement."""
    content = "This is a test [1] with citation."
    cites = ["http://example.com/paper1"]
    expected = "This is a test [[1]](http://example.com/paper1) with citation."
    assert llm.replace_citations(content, cites) == expected


def test_replace_citations_code_block():
    """Test citation replacement with code blocks."""
    content = "Text [1] ```print([1])``` more text [2]"
    cites = ["http://example.com/paper1", "http://example.com/paper2"]
    expected = (
        "Text [[1]](http://example.com/paper1) "
        "```print([1])``` more text [[2]](http://example.com/paper2)"
    )
    assert llm.replace_citations(content, cites) == expected


def test_replace_citations_inline_code():
    """Test citation replacement with inline code."""
    content = "Text [1] `code[1]` more text [2]"
    cites = ["http://example.com/paper1", "http://example.com/paper2"]
    expected = (
        "Text [[1]](http://example.com/paper1) "
        "`code[1]` more text [[2]](http://example.com/paper2)"
    )
    assert llm.replace_citations(content, cites) == expected


def test_replace_citations_unused():
    """Test handling of unused citations."""
    content = "Text [1]"
    cites = ["http://example.com/paper1", "http://example.com/paper2"]
    expected = (
        "Text [[1]](http://example.com/paper1)\n\n"
        "Additional citations: [[2]](http://example.com/paper2)"
    )
    assert llm.replace_citations(content, cites) == expected


def test_replace_citations_empty():
    """Test with empty content."""
    content = ""
    cites = ["http://example.com/paper1"]
    expected = "\n\nAdditional citations: [[1]](http://example.com/paper1)"
    assert llm.replace_citations(content, cites) == expected


def test_replace_citations_no_citations():
    """Test with no citations in content."""
    content = "Text without citations"
    cites = ["http://example.com/paper1"]
    expected = (
        "Text without citations\n\n"
        "Additional citations: [[1]](http://example.com/paper1)"
    )
    assert llm.replace_citations(content, cites) == expected


def test_replace_citations_with_parentheses():
    """Test URL encoding of parentheses in citations."""
    content = "Text [1] with citation."
    cites = ["http://example.com/paper(1)"]
    expected = "Text [[1]](http://example.com/paper%281%29) with citation."
    assert llm.replace_citations(content, cites) == expected
