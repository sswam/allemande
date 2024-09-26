import pytest
from word_frequency import word_count


"""
Demo test for word frequency count.
"""


def test_word_count():
    """
    Test the word_count function in the word_frequency module with sample input.
    """
    input_text = "hello world hello"
    expected_output = {
        "hello": 2,
        "world": 1,
    }

    response = word_count(input_text)

    assert response == expected_output

