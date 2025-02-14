import io
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import safety.safety as subject

subject_name = subject.__name__

@pytest.fixture
def mock_nsfw_words():
    return ["NSFW", "sexy", "nurse outfit"]

@pytest.fixture
def setup_safety(mock_nsfw_words):
    with patch(f'{subject_name}.NSFW_WORDS', mock_nsfw_words):
        subject.NSFW_WORDS_RE, subject.NSFW_PHRASE_RE = subject.compile_regexps(mock_nsfw_words)
        yield

def test_compile_regexps(mock_nsfw_words):
    word_re, phrase_re = subject.compile_regexps(mock_nsfw_words)
    assert "NSFW|sexy|nurse\\ outfit" in word_re
    assert r"\b(\w+)\b\s*" in phrase_re

def test_load_nsfw_words(tmp_path):
    test_file = tmp_path / "test_nsfw.txt"
    test_file.write_text("word1\nword2\nphrase with spaces")

    words = subject.load_nsfw_words([test_file])
    assert words == ["word1", "word2", "phrase with spaces"]

@pytest.mark.parametrize("input_text, expected", [
    ("", ""),
    ("Hello world", "Hello world"),
    ("This is NSFW content", ""),
    ("Hello sexy world", ""),
    ("A nurse outfit is nice", ""),
    ("# NSFW Section\nBad content\n\n# Safe Section\nGood content", "# Safe Section\nGood content"),
])
def test_remove_nsfw_text_basic(setup_safety, input_text, expected):
    result = subject.remove_nsfw_text(input_text)
    assert result.strip() == expected.strip()

@pytest.mark.parametrize("input_text, expected", [
    ("Hello sexy girls, ladies and gentlemen", "Hello ladies and gentlemen"),
    ("Men, sexy women, and children", "Men, and children"),
    ("Normal, NSFW, safe", "Normal, safe"),
    ("First, second, nurse outfit, fourth", "First, second, fourth"),
])
def test_remove_nsfw_text_lists(setup_safety, input_text, expected):
    result = subject.remove_nsfw_text(input_text)
    assert result.strip() == expected.strip()

def test_apply_adult_options():
    test_data = {
        "normal": "safe content",
        "filtered": "sexy content",
        "special_adult": "adult content",
        "nested": {
            "normal": "safe",
            "filtered": "NSFW",
            "special_adult": "more adult"
        }
    }

    # Test with adult=False
    data_safe = test_data.copy()
    with patch(f'{subject_name}.remove_nsfw_text', side_effect=lambda x: "FILTERED" if "NSFW" in x or "sexy" in x else x):
        subject.apply_adult_options(data_safe, False)
        assert data_safe["filtered"] == "FILTERED"
        assert "special_adult" not in data_safe
        assert data_safe["nested"]["filtered"] == "FILTERED"
        assert "special_adult" not in data_safe["nested"]

    # Test with adult=True
    data_adult = test_data.copy()
    subject.apply_adult_options(data_adult, True)
    assert data_adult["special"] == "adult content"
    assert data_adult["nested"]["special"] == "more adult"

def test_process_text():
    with patch(f'{subject_name}.safety_setup'):
        input_stream = io.StringIO("Hello sexy world")
        output_stream = io.StringIO()

        subject.process(input_stream, output_stream, adult=False)
        assert output_stream.getvalue().strip() == ""

def test_process_json():
    with patch(f'{subject_name}.safety_setup'):
        input_data = {
            "text": "Hello world",
            "filtered": "sexy content",
            "special_adult": "adult stuff"
        }
        input_stream = io.StringIO(str(input_data))
        output_stream = io.StringIO()

        with patch('json.load', return_value=input_data):
            subject.process(input_stream, output_stream, adult=False, is_json=True)
            assert "special_adult" not in output_stream.getvalue()
