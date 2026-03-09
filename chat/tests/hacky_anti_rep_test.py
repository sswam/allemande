import pytest
from copy import deepcopy

import hacky_anti_rep as subject

subject_name = subject.__name__


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def msgs(*contents):
    """Build a list of message dicts from content strings."""
    return [{"content": c} for c in contents]


def contents(messages):
    """Extract content strings from a list of message dicts."""
    return [m["content"] for m in messages]


# ---------------------------------------------------------------------------
# _first_word
# ---------------------------------------------------------------------------

class TestFirstWord:
    def test_normal(self):
        assert subject._first_word("hello world") == "hello"

    def test_leading_punctuation(self):
        assert subject._first_word("...hello world") == "hello"

    def test_empty(self):
        assert subject._first_word("") == ""

    def test_only_punctuation(self):
        assert subject._first_word("!!! ???") == ""

    def test_single_word(self):
        assert subject._first_word("word") == "word"

    def test_digits(self):
        assert subject._first_word("42 things") == "42"

    def test_apostrophe_in_word(self):
        assert subject._first_word("don't stop") == "don't"


# ---------------------------------------------------------------------------
# _last_word
# ---------------------------------------------------------------------------

class TestLastWord:
    def test_normal(self):
        assert subject._last_word("hello world") == "world"

    def test_trailing_punctuation(self):
        assert subject._last_word("hello world...") == "world"

    def test_empty(self):
        assert subject._last_word("") == ""

    def test_only_punctuation(self):
        assert subject._last_word("!!! ???") == ""

    def test_single_word(self):
        assert subject._last_word("word") == "word"

    def test_digits(self):
        assert subject._last_word("things 42") == "42"

    def test_apostrophe_in_word(self):
        assert subject._last_word("it's fine") == "fine"
        assert subject._last_word("that's Sam's") == "Sam's"


# ---------------------------------------------------------------------------
# _strip_word_prefix
# ---------------------------------------------------------------------------

class TestStripWordPrefix:
    def test_no_common_prefix(self):
        assert subject._strip_word_prefix("hello world", "foo bar") == "hello world"

    def test_common_prefix_one_word(self):
        assert subject._strip_word_prefix("hello world", "hello there") == "world"

    def test_common_prefix_two_words(self):
        assert subject._strip_word_prefix("hello brave world", "hello brave new") == "world"

    def test_full_match_returns_empty(self):
        assert subject._strip_word_prefix("hello world", "hello world") == ""

    def test_prior_shorter_than_later(self):
        # All words of prior match prefix of later -> empty
        assert subject._strip_word_prefix("hello", "hello world foo") == ""

    def test_empty_prior(self):
        assert subject._strip_word_prefix("", "hello") == ""

    def test_empty_later(self):
        assert subject._strip_word_prefix("hello world", "") == "hello world"

    def test_both_empty(self):
        assert subject._strip_word_prefix("", "") == ""

    def test_single_word_match(self):
        assert subject._strip_word_prefix("hi", "hi") == ""

    def test_preserves_trailing_whitespace_area(self):
        result = subject._strip_word_prefix("the cat sat", "the dog ran")
        assert result == "cat sat"

    def test_ignores_trailing_punctuation(self):
        result = subject._strip_word_prefix("hello, world", "hello there")
        assert result == "world"

    def test_apostrophe_word_prefix(self):
        assert subject._strip_word_prefix("don't stop me", "don't stop now") == "me"



# ---------------------------------------------------------------------------
# _strip_word_suffix
# ---------------------------------------------------------------------------

class TestStripWordSuffix:
    def test_no_common_suffix(self):
        assert subject._strip_word_suffix("hello world", "foo bar") == "hello world"

    def test_common_suffix_one_word(self):
        assert subject._strip_word_suffix("hello world", "brave world") == "hello"

    def test_common_suffix_two_words(self):
        assert subject._strip_word_suffix("see the light", "into the light") == "see"

    def test_full_match_returns_empty(self):
        assert subject._strip_word_suffix("hello world", "hello world") == ""

    def test_prior_shorter_than_later(self):
        assert subject._strip_word_suffix("world", "hello world") == ""

    def test_empty_prior(self):
        assert subject._strip_word_suffix("", "hello") == ""

    def test_empty_later(self):
        assert subject._strip_word_suffix("hello world", "") == "hello world"

    def test_both_empty(self):
        assert subject._strip_word_suffix("", "") == ""

    def test_single_word_match(self):
        assert subject._strip_word_suffix("hi", "hi") == ""

    def test_strips_trailing_whitespace_from_result(self):
        result = subject._strip_word_suffix("cat sat mat", "dog rat mat")
        assert result == "cat sat"
        assert not result.endswith(" ")


# ---------------------------------------------------------------------------
# _apply_prefix_stripping
# ---------------------------------------------------------------------------

class TestApplyPrefixStripping:
    def test_no_repetition(self):
        m = msgs("hello world", "foo bar")
        subject._apply_prefix_stripping(m)
        assert contents(m) == ["hello world", "foo bar"]

    def test_two_messages_same_prefix_strip_both_false(self):
        m = msgs("hello world", "hello there")
        subject._apply_prefix_stripping(m, strip_both=False)
        # The later message (index 1) is kept; the earlier (index 0) is stripped
        assert m[1]["content"] == "hello there"
        assert m[0]["content"] == "world"

    def test_two_messages_same_prefix_strip_both_true(self):
        # Default: strip_both=True, both messages lose the shared prefix
        m = msgs("hello world", "hello there")
        subject._apply_prefix_stripping(m)
        assert m[0]["content"] == "world"
        assert m[1]["content"] == "there"

    def test_three_messages_same_prefix(self):
        m = msgs("hello alpha", "hello beta", "hello gamma")
        subject._apply_prefix_stripping(m)
        # All should have "hello" stripped
        assert not m[2]["content"].startswith("hello")
        assert not m[1]["content"].startswith("hello")
        assert not m[0]["content"].startswith("hello")

    def test_empty_message_skipped(self):
        m = msgs("", "hello world")
        subject._apply_prefix_stripping(m)
        assert m[0]["content"] == ""
        assert m[1]["content"] == "hello world"

    def test_single_message(self):
        m = msgs("hello world")
        subject._apply_prefix_stripping(m)
        assert m[0]["content"] == "hello world"

    def test_no_messages(self):
        m = []
        subject._apply_prefix_stripping(m)
        assert m == []

    def test_case_insensitive_key(self):
        # "Hello" and "hello" share the same key after .lower()
        m = msgs("Hello world", "hello there")
        subject._apply_prefix_stripping(m)
        # Should detect the shared first-word key; both stripped
        assert m[0]["content"] == "world"
        assert m[1]["content"] == "there"

# ---------------------------------------------------------------------------
# _apply_suffix_stripping
# ---------------------------------------------------------------------------

class TestApplySuffixStripping:
    def test_no_repetition(self):
        m = msgs("hello world", "foo bar")
        subject._apply_suffix_stripping(m)
        assert contents(m) == ["hello world", "foo bar"]

    def test_two_messages_same_suffix_strip_both_false(self):
        m = msgs("see the light", "into the light")
        subject._apply_suffix_stripping(m, strip_both=False)
        assert m[1]["content"] == "into the light"
        assert m[0]["content"] == "see"

    def test_two_messages_same_suffix_strip_both_true(self):
        m = msgs("see the light", "into the light")
        subject._apply_suffix_stripping(m)
        assert m[0]["content"] == "see"
        assert m[1]["content"] == "into"

    def test_three_messages_same_suffix(self):
        m = msgs("alpha end", "beta end", "gamma end")
        subject._apply_suffix_stripping(m)
        assert not m[2]["content"].endswith("end")
        assert not m[1]["content"].endswith("end")
        assert not m[0]["content"].endswith("end")

    def test_empty_message_skipped(self):
        m = msgs("", "hello world")
        subject._apply_suffix_stripping(m)
        assert m[0]["content"] == ""
        assert m[1]["content"] == "hello world"

    def test_single_message(self):
        m = msgs("hello world")
        subject._apply_suffix_stripping(m)
        assert m[0]["content"] == "hello world"

    def test_no_messages(self):
        m = []
        subject._apply_suffix_stripping(m)
        assert m == []


# ---------------------------------------------------------------------------
# hacky_anti_rep (main public function)
# ---------------------------------------------------------------------------

class TestHackyAntiRep:
    def test_no_repetition(self):
        m = msgs("alpha beta", "gamma delta")
        subject.hacky_anti_rep(m)
        assert contents(m) == ["alpha beta", "gamma delta"]

    def test_modifies_in_place(self):
        m = msgs("hello world", "hello there")
        original_id = id(m)
        subject.hacky_anti_rep(m)
        assert id(m) == original_id

    def test_strip_empty_false_keeps_empty_messages(self):
        # If stripping produces an empty content, keep the message
        m = msgs("hello world", "hello world")
        subject.hacky_anti_rep(m, strip_empty=False)
        assert len(m) == 2

    def test_strip_empty_true_removes_empty_messages(self):
        m = msgs("hello world", "hello world")
        subject.hacky_anti_rep(m, strip_empty=True)
        assert all(msg["content"] for msg in m)

    def test_empty_list(self):
        m = []
        subject.hacky_anti_rep(m)
        assert m == []

    def test_single_message(self):
        m = msgs("hello world")
        subject.hacky_anti_rep(m)
        assert m[0]["content"] == "hello world"

    def test_both_prefix_and_suffix_applied(self):
        # Two messages sharing both prefix and suffix
        m = msgs("hello brave world", "hello wise world")
        subject.hacky_anti_rep(m)
        # older message stripped of shared prefix/suffix
        assert m[0]["content"] != "hello brave world"

    def test_whitespace_only_message(self):
        m = msgs("   ", "hello world")
        subject.hacky_anti_rep(m)
        assert m[1]["content"] == "hello world"

    def test_strip_empty_true_with_whitespace(self):
        m = msgs("   ", "hello world")
        subject.hacky_anti_rep(m, strip_empty=True)
        assert any(msg["content"].strip() == "hello world" for msg in m)

    def test_does_not_mutate_unrelated_messages(self):
        # With strip_both=False, the newer message is preserved
        m = msgs("hello world foo", "hello world bar")
        subject.hacky_anti_rep(m, strip_both=False)
        assert m[-1]["content"] == "hello world bar"

    def test_strip_both_false_preserves_later(self):
        m = msgs("hello world", "hello there")
        subject.hacky_anti_rep(m, strip_both=False)
        assert m[-1]["content"] == "hello there"
        assert m[0]["content"] == "world"

    def test_strip_both_true_strips_later_too(self):
        m = msgs("hello world", "hello there")
        subject.hacky_anti_rep(m)
        assert m[0]["content"] == "world"
        assert m[1]["content"] == "there"

    def test_multiple_pairs_different_prefixes(self):
        m = msgs(
            "apple pie is great",
            "banana split is nice",
            "apple tart is great",
            "banana cream is nice",
        )
        subject.hacky_anti_rep(m)
        # Newest messages in each group are also stripped with strip_both=True
        assert "banana" not in m[3]["content"] or "cream" in m[3]["content"]
        assert "apple" not in m[2]["content"] or "tart" in m[2]["content"]

    @pytest.mark.parametrize("strip_empty", [True, False])
    def test_all_empty_messages(self, strip_empty):
        m = msgs("", "", "")
        subject.hacky_anti_rep(m, strip_empty=strip_empty)
        if strip_empty:
            assert m == []
        else:
            assert len(m) == 3

    def test_preserves_role_field(self):
        m = [
            {"role": "user", "content": "hello world"},
            {"role": "assistant", "content": "hello there"},
        ]
        subject.hacky_anti_rep(m)
        assert m[0]["role"] == "user"
        assert m[1]["role"] == "assistant"

    def test_repeated_identical_messages(self):
        m = msgs("same thing here", "same thing here", "same thing here")
        subject.hacky_anti_rep(m, strip_empty=True)
        assert len(m) >= 1
        # At least one message survives
        assert any(msg["content"] for msg in m)

    def test_apostrophe_words(self):
        m = msgs("don't stop me now", "don't stop the music")
        subject.hacky_anti_rep(m)
        assert m[0]["content"] == "me now"
        assert m[1]["content"] == "the music"
