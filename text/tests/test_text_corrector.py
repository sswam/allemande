import pytest
from text_corrector import TextCorrector

@pytest.fixture
def corrector():
    return TextCorrector()

def test_preprocess(corrector):
    assert corrector.preprocess("H3ll0 W0rld") == "Hello World"

def test_get_best_guess_sentence(corrector):
    assert corrector.get_best_guess_sentence("H33ll0 HHTTP W0rld brognatzklfjqwper") == "Hello HTTP World [brognatzklfjqwper]"
