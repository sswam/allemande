import os

# disable DeprecationWarning https://github.com/jupyter/jupyter_core/issues/398
os.environ["JUPYTER_PLATFORM_DIRS"] = "1"

import io
import pytest
from unittest.mock import patch, MagicMock

import hello_py as subject
subject_main = subject.hello_py

def test_analyze_sentiment():
    assert subject.analyze_sentiment("I'm happy") == 'Positive'
    assert subject.analyze_sentiment("I'm sad") == 'Negative'
    assert subject.analyze_sentiment("I'm so-so") == 'Neutral'

@pytest.mark.parametrize("feeling, expected_sentiment", [
    ("I'm feeling great!", "I hope you have a great day!"),
    ("I'm feeling terrible.", "I hope you feel better soon."),
    ("I'm so-so baloney sandwich.", "Life has its ups and downs, hope yours swings up!"),
])
def test_reply_sentiment(feeling, expected_sentiment):
    assert subject.reply_sentiment(feeling) == expected_sentiment

@patch('llm.query')
def test_reply_ai(mock_query):
    mock_query.return_value = "I'm glad you're feeling good, John!"
    response = subject.reply_ai("John", "I'm feeling good", "clia")
    assert "I'm glad you're feeling good, John!" in response

@pytest.mark.parametrize("feeling, ai, expected_response", [
    ("I'm happy", False, "I hope you have a great day!"),
    ("I'm sad", False, "I hope you feel better soon."),
    ("I'm so-so", False, "Life has its ups and downs, hope yours swings up!"),
    ("I'm feeling great", True, "I'm glad you're feeling great!"),
])
def test_hello_py(feeling, ai, expected_response):
    input_stream = io.StringIO(feeling + "\n")
    output_stream = io.StringIO()

    with patch('llm.query', return_value="I'm glad you're feeling great!"):
        subject_main(istream=input_stream, ostream=output_stream, name="Test", ai=ai)

    output = output_stream.getvalue()
    assert "Hello, Test" in output
    assert "How are you feeling?" in output
    assert expected_response in output

@pytest.mark.parametrize("fortune_word", ["", "lucky", "unlucky", "fortunate", "unfortunate"])
def test_hello_py_fortune_words(fortune_word):
    input_stream = io.StringIO(f"{fortune_word}\n")
    output_stream = io.StringIO()

    subject_main(istream=input_stream, ostream=output_stream, name="Test")

    output = output_stream.getvalue()
    assert "Hello, Test" in output
    assert "How are you feeling?" in output

    print(output)

    # can't test fortune, and can't see to mock it either
    assert "I hope you have a great day!" not in output
    assert "I hope you feel better soon." not in output
    assert "Life has its ups and downs, hope yours swings up!" not in output


"""
Important Notes for AI:

We are using subject and subject_main to refer to the module, to make the test
code more generic and so we won't need to change much if we rename the module.
"""
