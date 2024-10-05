import pytest
from text_safety import SafetyChecker

@pytest.fixture
def checker():
    return SafetyChecker({"obscene", "profane", "bad dog"})

def test_load_nsfw_phrases(checker):
    assert "obscene" in checker.nsfw_phrases
    assert "profane" in checker.nsfw_phrases

def test_check_safety(checker):
    result = checker.check_safety(["this", "is", "a", "bad", "dog"])
    assert "bad dog" in result

def test_check_safety_no_match(checker):
    result = checker.check_safety(["this", "is", "a", "good", "sentence"])
    assert len(result) == 0
