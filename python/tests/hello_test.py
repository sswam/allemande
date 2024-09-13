import io
import pytest
import sh
from unittest.mock import patch
from hello import hello, analyze_sentiment

def test_analyze_sentiment():
    assert analyze_sentiment("I'm happy") == 'Positive'
    assert analyze_sentiment("I'm sad") == 'Negative'
    assert analyze_sentiment("I'm so-so") == 'Neutral'

@pytest.mark.parametrize("feeling, expected_sentiment", [
    ("I'm feeling great!", "I hope you have a great day!"),
    ("I'm feeling terrible.", "I hope you feel better soon."),
    ("I'm so-so baloney sandwich.", "Life has its ups and downs, hope yours swings up!"),
])
def test_hello_sentiment_response(feeling, expected_sentiment):
    input_stream = io.StringIO(feeling + "\n")
    output_stream = io.StringIO()

    hello(istream=input_stream, ostream=output_stream, name="Test")

    output = output_stream.getvalue()
    assert "Hello, Test" in output
    assert "How are you feeling?" in output
    assert expected_sentiment in output

@patch('sh.fortune')
def test_hello_fortune_response(mock_fortune):
    mock_fortune.return_value = "Your lucky numbers are 10, 20, 30."

    input_stream = io.StringIO("lucky\n")
    output_stream = io.StringIO()

    hello(istream=input_stream, ostream=output_stream, name="Test")

    output = output_stream.getvalue()
    assert "Hello, Test" in output
    assert "How are you feeling?" in output
    assert "Your lucky numbers are 10, 20, 30." in output

def test_hello_empty_response():
    input_stream = io.StringIO("\n")
    output_stream = io.StringIO()

    with patch('sh.fortune', return_value="A journey of a thousand miles begins with a single step."):
        hello(istream=input_stream, ostream=output_stream, name="Test")

    output = output_stream.getvalue()
    assert "Hello, Test" in output
    assert "How are you feeling?" in output
    assert "A journey of a thousand miles begins with a single step." in output

@pytest.mark.parametrize("fortune_word", ["lucky", "unlucky", "fortunate", "unfortunate"])
def test_hello_fortune_words(fortune_word):
    input_stream = io.StringIO(f"{fortune_word}\n")
    output_stream = io.StringIO()

    with patch('sh.fortune', return_value="The future looks bright."):
        hello(istream=input_stream, ostream=output_stream, name="Test")

    output = output_stream.getvalue()
    assert "Hello, Test" in output
    assert "How are you feeling?" in output
    assert "The future looks bright." in output
