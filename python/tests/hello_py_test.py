import os
import io
import pytest
from unittest.mock import patch, MagicMock
from typing import Any

import hello_py as subject  # type: ignore

subject_name = subject.__name__

def test_analyze_sentiment():
    assert subject.analyze_sentiment("I'm happy") == 'Positive'
    assert subject.analyze_sentiment("I'm sad") == 'Negative'
    assert subject.analyze_sentiment("I'm so-so") == 'Neutral'

@pytest.mark.parametrize("feeling, expected_sentiment", [
    ("I'm feeling great!", "I'm glad to hear that! I hope your day continues to be great!"),
    ("I'm feeling terrible.", "I'm sorry to hear that. Remember, things can always get better."),
    ("I'm so-so baloney sandwich.", "I see. Life has its ups and downs, I hope things improve for you soon!"),
])
def test_reply_sentiment(feeling, expected_sentiment):
    assert subject.reply_sentiment(feeling) == expected_sentiment

@patch('llm.query')
def test_reply_ai(mock_query):
    mock_query.return_value = "I'm glad you're feeling good, John!"
    response = subject.reply_ai("John", "I'm feeling good", "clia")
    assert "I'm glad you're feeling good, John!" in response

@pytest.mark.parametrize("feeling, ai, expected_response", [
    ("I'm happy", False, "I'm glad to hear that! I hope your day continues to be great!"),
    ("I'm sad", False, "I'm sorry to hear that. Remember, things can always get better."),
    ("I'm so-so", False, "I see. Life has its ups and downs, I hope things improve for you soon!"),
    ("I'm feeling great", True, "I'm glad you're feeling great!"),
])
def test_hello(feeling, ai, expected_response):
    input_stream = io.StringIO(feeling + "\n")
    output_stream = io.StringIO()

    def mock_get():
        return input_stream.readline().strip()

    def mock_put(text):
        output_stream.write(text + "\n")

    with patch('llm.query', return_value="I'm glad you're feeling great!"):
        subject.hello(get=mock_get, put=mock_put, name="Test", ai=ai)

    output = output_stream.getvalue()
    assert "Hello, Test!" in output
    assert "How are you feeling today?" in output
    assert expected_response in output

@pytest.mark.parametrize("fortune_word", ["", "lucky", "unlucky", "fortunate", "unfortunate"])
def test_hello_fortune_words(fortune_word):
    input_stream = io.StringIO(f"{fortune_word}\n")
    output_stream = io.StringIO()

    def mock_get():
        return input_stream.readline().strip()

    def mock_put(text):
        output_stream.write(text + "\n")

    subject.hello(get=mock_get, put=mock_put, name="Test")

    output = output_stream.getvalue()
    assert "Hello, Test!" in output
    assert "How are you feeling today?" in output

    print(output)

    assert "I hope you have a great day!" not in output
    assert "I hope you feel better soon." not in output
    assert "Life has its ups and downs, hope yours swings up!" not in output

@patch(f'{subject_name}.reply_fortune')
def test_hello_with_fortune(mock_reply_fortune):
    mock_reply_fortune.return_value = "A fortune cookie message"

    input_stream = io.StringIO("lucky\n")
    output_stream = io.StringIO()

    def mock_get():
        return input_stream.readline().strip()

    def mock_put(text):
        output_stream.write(text + "\n")

    subject.hello(get=mock_get, put=mock_put, name="Test")

    mock_reply_fortune.assert_called_once()
    output = output_stream.getvalue()
    assert "Hello, Test!" in output
    assert "How are you feeling today?" in output
    assert "A fortune cookie message" in output


"""
## Important Notes for AI [DO NOT COPY THEM IN YOUR OUTPUT, it gets EXPENSIVE FOR ME!]:

- We are using subject and subject_main to refer to the module, to make the
  code more generic and so we can rename the module easily.

- Include tests for small and degenerate cases: empty string, empty list,
  single element list, None (if appropriate), etc.

- When working with numbers, remember to test 0 and 1, we might get / by zero.

- You can see the code to be tested, so test anything that looks like it might break it.

## Ideas for future, might need helper functions (go ahead and write some if you need them!)

- performance test / benchmark code that might be slow, or must be fast

- for async code, if it should not block much, test that it does not

- use the ally.quote library for quoting blocks of text
"""
