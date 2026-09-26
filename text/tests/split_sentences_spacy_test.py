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
def spacy_splitter(nlp):
	"""Return a spaCy-based splitter."""
	return lambda text: subject.split_sentences_spacy(text, nlp)


# Tests for split_sentences_spacy
def test_spacy_basic_sentences(spacy_splitter):
	"""Test spaCy sentence splitting."""
	result = list(spacy_splitter("Hello world. How are you?"))
	assert len(result) == 2
	assert "Hello world." in result[0]
	assert "How are you?" in result[1]


def test_spacy_with_abbreviations(spacy_splitter):
	"""Test that spaCy handles abbreviations correctly."""
	result = list(spacy_splitter("Dr. Smith went to the store. He bought milk."))
	assert len(result) == 2


def test_spacy_edge_cases(spacy_splitter):
	"""Test spaCy with edge cases."""
	assert list(spacy_splitter("")) == []
	assert len(list(spacy_splitter("No punctuation"))) == 1


# Tests for format_sentences_as_lines
def test_format_sentences_basic_spacy(nlp):
	"""Test formatting sentences from spaCy."""
	splitter = lambda text: subject.split_sentences_spacy(text, nlp)
	text = "Hello world. How are you?"
	result = list(subject.format_sentences_as_lines(StringIO(text), splitter))
	assert "Hello world." in result
	assert "How are you?" in result


# Tests for split_sentences_test helper
def test_split_sentences_test_spacy(nlp):
	"""Test the split_sentences_test helper with spaCy."""
	splitter = lambda text: subject.split_sentences_spacy(text, nlp)
	assert subject.split_sentences_test("Hello\nworld.", splitter) == "Hello world."
	assert subject.split_sentences_test("", splitter) == ""
	assert subject.split_sentences_test("Two. Sentences.", splitter) == "Two.\nSentences."
	assert subject.split_sentences_test("- foo\n- bar", splitter) == "- foo\n- bar"


def test_integration_spacy_full_workflow(nlp):
	"""Test complete workflow with spaCy."""
	splitter = lambda text: subject.split_sentences_spacy(text, nlp)
	text = """
Dr. Smith went to the store. He bought milk.

Then he went home.
""".strip()

	result = subject.split_sentences_test(text, splitter)

	# Should split sentences
	assert "Dr. Smith went to the store." in result or "Dr. Smith went to the store" in result
	assert "He bought milk." in result or "He bought milk" in result


if __name__ == "__main__":
	pytest.main([__file__, "-v"])
