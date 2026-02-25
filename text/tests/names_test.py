import io
import pytest
from unittest.mock import patch

import names as subject  # type: ignore

subject_name = subject.__name__


# --- extract_partial_names ---

def test_extract_partial_names_single_word():
    assert subject.extract_partial_names("Alice") == ["Alice"]

def test_extract_partial_names_two_words():
    assert subject.extract_partial_names("Alice Smith") == ["Alice", "Alice Smith"]

def test_extract_partial_names_three_words():
    assert subject.extract_partial_names("Alice B Smith") == ["Alice", "Alice B", "Alice B Smith"]

def test_extract_partial_names_four_words():
    result = subject.extract_partial_names("Alice B C Smith")
    assert result == ["Alice", "Alice B", "Alice B C", "Alice B C Smith"]

def test_extract_partial_names_empty_string():
    # split() of empty string is [], so range produces nothing
    assert subject.extract_partial_names("") == []

def test_extract_partial_names_strips_trailing_punctuation():
    result = subject.extract_partial_names("Smith.")
    assert result == ["Smith"]

def test_extract_partial_names_strips_trailing_dash():
    result = subject.extract_partial_names("Smith-")
    assert result == ["Smith"]

def test_extract_partial_names_strips_trailing_apostrophe():
    result = subject.extract_partial_names("O'Brien'")
    assert result == ["O'Brien"]

def test_extract_partial_names_strips_trailing_underscore():
    result = subject.extract_partial_names("Smith_")
    assert result == ["Smith"]

def test_extract_partial_names_multi_trailing_punct():
    result = subject.extract_partial_names("Smith...")
    assert result == ["Smith"]

def test_extract_partial_names_internal_punct_preserved():
    result = subject.extract_partial_names("O'Brien")
    assert result == ["O'Brien"]

def test_extract_partial_names_hyphenated_preserved():
    result = subject.extract_partial_names("Smith-Jones")
    assert result == ["Smith-Jones"]


# --- extract_names (integration) ---

def run_extract(text: str) -> list[str]:
    istream = io.StringIO(text)
    ostream = io.StringIO()
    subject.extract_names(istream, ostream)
    output = ostream.getvalue()
    return [line for line in output.splitlines() if line]


def test_extract_names_empty_input():
    assert run_extract("") == []

def test_extract_names_no_names():
    result = run_extract("hello world, nothing to see here.")
    assert result == []

def test_extract_names_single_capitalized_word():
    result = run_extract("Alice went to the market.")
    assert "Alice" in result

def test_extract_names_two_word_name():
    result = run_extract("Alice Smith went shopping.")
    assert "Alice" in result
    assert "Alice Smith" in result

def test_extract_names_three_word_name():
    result = run_extract("Mary Jane Watson smiled.")
    assert "Mary" in result
    assert "Mary Jane" in result
    assert "Mary Jane Watson" in result

def test_extract_names_lowercase_only():
    result = run_extract("this is all lowercase text.")
    assert result == []

def test_extract_names_at_mention_single():
    result = run_extract("Hello @alice!")
    assert any("@alice" in r for r in result)

def test_extract_names_at_mention_multi_word():
    result = run_extract("Ping @alice bob.")
    assert any("@alice" in r for r in result)

def test_extract_names_multiple_names():
    result = run_extract("Alice and Bob met Charlie.")
    assert "Alice" in result
    assert "Bob" in result
    assert "Charlie" in result

def test_extract_names_number_as_first_char():
    # Numbers can start a "name" per the pattern [A-Z0-9]
    result = run_extract("3Com is a company.")
    assert any("3Com" in r for r in result)

def test_extract_names_newlines():
    result = run_extract("Alice\nBob\nCharlie\n")
    assert "Alice" in result
    assert "Bob" in result
    assert "Charlie" in result

def test_extract_names_output_has_newline_per_name():
    istream = io.StringIO("Alice Smith")
    ostream = io.StringIO()
    subject.extract_names(istream, ostream)
    output = ostream.getvalue()
    lines = output.splitlines()
    assert len(lines) >= 1
    for line in lines:
        assert line  # no blank lines

def test_extract_names_hyphenated_name():
    result = run_extract("Mary-Jane visited us.")
    assert any("Mary-Jane" in r for r in result)

def test_extract_names_with_apostrophe():
    result = run_extract("O'Brien arrived late.")
    assert any("O'Brien" in r for r in result)

def test_extract_names_stop_words_not_included_as_names():
    # Common stop words like "the", "and", "or" should not appear as standalone names
    result = run_extract("the and or with")
    assert "the" not in result
    assert "and" not in result

def test_extract_names_four_word_at_mention():
    result = run_extract("@alice bob carol dave")
    # Should match @alice and possibly more words
    assert any(r.startswith("@alice") for r in result)

def test_extract_names_sentence_with_punctuation():
    result = run_extract("Hello, Alice! How are you?")
    assert "Alice" in result

def test_extract_names_all_caps():
    result = run_extract("NASA launched a rocket.")
    assert "NASA" in result

def test_extract_names_mixed_case_middle_words():
    # Middle words can be lowercase; only first and last must be capitalized
    result = run_extract("John van Dyke spoke.")
    assert "John" in result
    # "John van" may or may not match depending on pattern, but John should always be there

def test_extract_names_does_not_crash_on_unicode():
    result = run_extract("Ångström is a unit. José arrived.")
    # Should not raise; result may or may not contain names depending on regex
    assert isinstance(result, list)

def test_extract_names_repeated_name():
    result = run_extract("Alice met Alice again.")
    assert result.count("Alice") >= 2

def test_extract_names_at_mention_at_start():
    result = run_extract("@Bob please review this.")
    assert any(r.startswith("@Bob") for r in result)

def test_extract_names_long_text():
    text = "Alice Smith and Bob Jones met Carol White for lunch. David Brown arrived late."
    result = run_extract(text)
    assert "Alice" in result
    assert "Alice Smith" in result
    assert "Bob" in result
    assert "Bob Jones" in result
    assert "Carol" in result
    assert "David" in result
    assert "David Brown" in result

def test_extract_names_possessive():
    result = run_extract("Alice's bag was found.")
    assert "Alice" in result
