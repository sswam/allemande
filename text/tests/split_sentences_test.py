#!/usr/bin/env python3-allemande

import pytest
from io import StringIO
from unittest.mock import MagicMock

import split_sentences as subject

subject_name = subject.__name__


@pytest.fixture
def nlp():
	"""Load spaCy model for testing."""
	import spacy
	return spacy.load("en_core_web_sm")


@pytest.fixture
def simple_segmenter():
	"""Return the simple regex-based segmenter."""
	return subject.segment_text_into_sentences_simple


@pytest.fixture
def spacy_segmenter(nlp):
	"""Return a spaCy-based segmenter."""
	return lambda text: subject.segment_text_into_sentences_spacy(text, nlp)


# Tests for segment_text_into_sentences_simple
def test_simple_basic_sentences(simple_segmenter):
	"""Test simple sentence splitting."""
	result = list(simple_segmenter("Hello world. How are you?"))
	assert result == ["Hello world.", "How are you?"]


def test_simple_with_abbreviations(simple_segmenter):
	"""Test that common abbreviations don't trigger splits."""
	result = list(simple_segmenter("Dr. Smith went to the store. He bought milk."))
	assert result == ["Dr. Smith went to the store.", "He bought milk."]

	result = list(simple_segmenter("The U.S. economy is strong. Markets are up."))
	assert result == ["The U.S. economy is strong.", "Markets are up."]

	result = list(simple_segmenter("It costs $5.99 each. That's expensive."))
	assert result == ["It costs $5.99 each.", "That's expensive."]


def test_simple_with_multiple_punctuation(simple_segmenter):
	"""Test sentences with multiple periods or punctuation."""
	result = list(simple_segmenter("What?! Really?! I can't believe it!"))
	assert result == ["What?!", "Really?!", "I can't believe it!"]

	result = list(simple_segmenter("Wait... Something's wrong. Check again."))
	assert len(result) == 2
	assert "Wait..." in result[0]
	assert "Check again." in result[1]


def test_simple_exclamation_and_question(simple_segmenter):
	"""Test exclamation and question marks."""
	result = list(simple_segmenter("Stop! Don't go there! It's dangerous!"))
	assert result == ["Stop!", "Don't go there!", "It's dangerous!"]

	result = list(simple_segmenter("Really? Are you sure? I don't believe it."))
	assert result == ["Really?", "Are you sure?", "I don't believe it."]


def test_simple_edge_cases(simple_segmenter):
	"""Test edge cases."""
	assert list(simple_segmenter("")) == []
	assert list(simple_segmenter("No punctuation")) == ["No punctuation"]
	assert list(simple_segmenter("One.")) == ["One."]
	assert list(simple_segmenter("   ")) == []


def test_simple_multiple_exceptions_in_sentence(simple_segmenter):
	"""Test sentences with multiple abbreviations."""
	result = list(simple_segmenter("Dr. Smith and Prof. Jones met at 3 p.m. yesterday. They discussed Ph.D. requirements."))
	assert len(result) == 2
	assert "Dr. Smith and Prof. Jones met at 3 p.m. yesterday." in result[0]
	assert "They discussed Ph.D. requirements." in result[1]


def test_simple_lowercase_after_period(simple_segmenter):
	"""Test that lowercase after period doesn't split (like in decimals)."""
	result = list(simple_segmenter("The value is 3.14159 approximately."))
	assert len(result) == 1


def test_simple_end_of_string_punctuation(simple_segmenter):
	"""Test punctuation at end of string."""
	result = list(simple_segmenter("This is the end."))
	assert result == ["This is the end."]

	result = list(simple_segmenter("This is the end!"))
	assert result == ["This is the end!"]

	result = list(simple_segmenter("Is this the end?"))
	assert result == ["Is this the end?"]


# Tests for segment_text_into_sentences_spacy
def test_spacy_basic_sentences(spacy_segmenter):
	"""Test spaCy sentence splitting."""
	result = list(spacy_segmenter("Hello world. How are you?"))
	assert len(result) == 2
	assert "Hello world." in result[0]
	assert "How are you?" in result[1]


def test_spacy_with_abbreviations(spacy_segmenter):
	"""Test that spaCy handles abbreviations correctly."""
	result = list(spacy_segmenter("Dr. Smith went to the store. He bought milk."))
	assert len(result) == 2


def test_spacy_edge_cases(spacy_segmenter):
	"""Test spaCy with edge cases."""
	assert list(spacy_segmenter("")) == []
	assert len(list(spacy_segmenter("No punctuation"))) == 1


# Tests for group_lines_into_paragraphs
def test_group_lines_basic():
	"""Test basic paragraph grouping."""
	lines = ["Line one", "Line two", "", "Line three"]
	result = list(subject.group_lines_into_paragraphs(lines))
	assert len(result) == 2
	assert "Line one Line two" in result[0]
	assert "Line three" in result[1]


def test_group_lines_bullet_points():
	"""Test that bullet points are preserved."""
	lines = ["- Item one", "- Item two", "", "Regular line"]
	result = list(subject.group_lines_into_paragraphs(lines))
	assert len(result) == 2
	assert "- Item one\n" in result[0]
	assert "- Item two\n" in result[0]
	assert "Regular line" in result[1]


def test_group_lines_empty_input():
	"""Test with empty input."""
	assert list(subject.group_lines_into_paragraphs([])) == []


def test_group_lines_only_blank_lines():
	"""Test with only blank lines."""
	lines = ["", "", ""]
	result = list(subject.group_lines_into_paragraphs(lines))
	# Should produce empty paragraphs
	assert all(r.strip() == "" for r in result)


def test_group_lines_various_bullets():
	"""Test various bullet point styles."""
	lines = ["- Dash", "* Asterisk", "• Bullet", "◦ White bullet", "‣ Triangle"]
	result = list(subject.group_lines_into_paragraphs(lines))
	assert len(result) == 1
	for bullet_line in lines:
		assert bullet_line in result[0]


# Tests for format_sentences_as_lines
def test_format_sentences_basic_spacy(nlp):
	"""Test formatting sentences from spaCy."""
	segmenter = lambda text: subject.segment_text_into_sentences_spacy(text, nlp)
	text = "Hello world. How are you?"
	result = list(subject.format_sentences_as_lines(StringIO(text), segmenter))
	assert "Hello world." in result
	assert "How are you?" in result


def test_format_sentences_basic_simple(simple_segmenter):
	"""Test formatting sentences with simple segmenter."""
	text = "Hello world. How are you?"
	result = list(subject.format_sentences_as_lines(StringIO(text), simple_segmenter))
	assert "Hello world." in result
	assert "How are you?" in result


def test_format_sentences_with_paragraphs(simple_segmenter):
	"""Test formatting with multiple paragraphs."""
	text = "First para. Two sentences.\n\nSecond para. Also two."
	result = list(subject.format_sentences_as_lines(StringIO(text), simple_segmenter))
	# Should have blank line between paragraphs
	assert "" in result
	assert len([r for r in result if r]) >= 4  # At least 4 sentences


def test_format_sentences_preserves_bullets(simple_segmenter):
	"""Test that bullet points are preserved."""
	text = "- Item one\n- Item two"
	result = list(subject.format_sentences_as_lines(StringIO(text), simple_segmenter))
	assert any("- Item one" in r for r in result)
	assert any("- Item two" in r for r in result)


def test_format_sentences_empty_input(simple_segmenter):
	"""Test with empty input."""
	result = list(subject.format_sentences_as_lines(StringIO(""), simple_segmenter))
	assert result == []


def test_format_sentences_from_string(simple_segmenter):
	"""Test that string input works (not just StringIO)."""
	text = "Hello. World."
	result = list(subject.format_sentences_as_lines(text, simple_segmenter))
	assert "Hello." in result
	assert "World." in result


# Tests for split_sentences_test helper
def test_split_sentences_test_spacy(nlp):
	"""Test the split_sentences_test helper with spaCy."""
	segmenter = lambda text: subject.segment_text_into_sentences_spacy(text, nlp)
	assert subject.split_sentences_test("Hello\nworld.", segmenter) == "Hello world."
	assert subject.split_sentences_test("", segmenter) == ""
	assert subject.split_sentences_test("Two. Sentences.", segmenter) == "Two.\nSentences."
	assert subject.split_sentences_test("- foo\n- bar", segmenter) == "- foo\n- bar"


def test_split_sentences_test_simple(simple_segmenter):
	"""Test the split_sentences_test helper with simple segmenter."""
	assert subject.split_sentences_test("Hello\nworld.", simple_segmenter) == "Hello world."
	assert subject.split_sentences_test("", simple_segmenter) == ""
	assert subject.split_sentences_test("Two. Sentences.", simple_segmenter) == "Two.\nSentences."
	assert subject.split_sentences_test("- foo\n- bar", simple_segmenter) == "- foo\n- bar"


def test_split_sentences_test_complex_example(simple_segmenter):
	"""Test with a more complex example."""
	text = "Dr. Smith said hello. Then he left. Mr. Jones arrived at 3 p.m. yesterday."
	result = subject.split_sentences_test(text, simple_segmenter)
	lines = result.split("\n")
	assert len(lines) == 3
	assert "Dr. Smith said hello." in lines[0]
	assert "Then he left." in lines[1]
	assert "Mr. Jones arrived at 3 p.m. yesterday." in lines[2]


# Integration tests
def test_integration_simple_full_workflow(simple_segmenter):
	"""Test complete workflow with simple segmenter."""
	text = """
Dr. Smith went to the U.S. embassy. He met with officials there.

Later, Prof. Jones called at 3 p.m. They discussed important matters.

- Point one
- Point two

Final paragraph here.
""".strip()

	result = subject.split_sentences_test(text, simple_segmenter)
	lines = result.split("\n")

	# Should have sentences split properly
	assert "Dr. Smith went to the U.S. embassy." in result
	assert "He met with officials there." in result

	# Should preserve bullet points
	assert "- Point one" in result
	assert "- Point two" in result

	# Should have blank lines between paragraphs
	assert "" in lines


def test_integration_spacy_full_workflow(nlp):
	"""Test complete workflow with spaCy."""
	segmenter = lambda text: subject.segment_text_into_sentences_spacy(text, nlp)
	text = """
Dr. Smith went to the store. He bought milk.

Then he went home.
""".strip()

	result = subject.split_sentences_test(text, segmenter)

	# Should split sentences
	assert "Dr. Smith went to the store." in result or "Dr. Smith went to the store" in result
	assert "He bought milk." in result or "He bought milk" in result


if __name__ == "__main__":
	pytest.main([__file__, "-v"])

# Here's the test file for `split_sentences.py`:

# This test file includes:
#
# 1. **Tests for `segment_text_into_sentences_simple`**:
# - Basic sentence splitting
# - Handling of abbreviations (Dr., Prof., U.S., etc.)
# - Multiple punctuation marks (!!!, ?!, ...)
# - Edge cases (empty string, no punctuation, single sentence)
# - Multiple exceptions in one sentence
# - End-of-string punctuation
#
# 2. **Tests for `segment_text_into_sentences_spacy`**:
# - Basic functionality
# - Abbreviation handling
# - Edge cases
#
# 3. **Tests for `group_lines_into_paragraphs`**:
# - Basic line grouping
# - Bullet point preservation (-, *, •, etc.)
# - Empty input
# - Various bullet styles
#
# 4. **Tests for `format_sentences_as_lines`**:
# - Basic formatting
# - Multiple paragraphs
# - Bullet point preservation
# - String vs StringIO input
#
# 5. **Tests for `split_sentences_test`** (the helper function):
# - Both spaCy and simple segmenter versions
# - Complex examples
#
# 6. **Integration tests**:
# - Full workflow testing with realistic text
# - Both simple and spaCy segmenters
#
# The tests cover edge cases, degenerate inputs (empty strings, single elements), and the new simple splitter functionality you requested!
