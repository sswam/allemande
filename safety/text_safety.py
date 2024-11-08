#!/usr/bin/env python3-allemande

"""
safety_checker.py - A module for checking the safety of text content.
"""

import os
import re
from collections import defaultdict
import logging
from typing import Dict, List, Set
from pathlib import Path

from argh import arg

from ally import text
from text_corrector import TextCorrector

__version__ = "1.0.0"

NSFW_PHRASES = Path(os.environ["ALLEMANDE_HOME"])/"safety"/"nsfw_words"/"en"

logger = logging.getLogger(__name__)

class SafetyChecker:
    def __init__(self, nsfw_phrases: Set[str]):
        self.nsfw_phrases = nsfw_phrases
        self.max_phrase_length = max(len(phrase.split()) for phrase in self.nsfw_phrases)

    def check_safety(self, words: List[str]) -> Dict[str, List[str]]:
        potential_nsfw = defaultdict(list)

        # Check for single words and phrases
        for n in range(1, self.max_phrase_length + 1):
            for i in range(len(words) - n + 1):
                phrase = ' '.join(words[i:i+n])
                if phrase in self.nsfw_phrases:
                    potential_nsfw[phrase].append(phrase)

        return dict(potential_nsfw)

checker = None

def check(text: str):
    if not checker:
        nsfw_phrases = text.read_lines(NSFW_PHRASES, lower=True)
        checker = SafetyChecker(nsfw_phrases)
    nsfw_words = set()
    for phrase in nsfw_phrases:
        nsfw_words.update(phrase.split())
    corrector = TextCorrector(extra_words=nsfw_words)
    corrected_text = corrector.get_best_guess_sentence(text)
    words = re.findall(r'\b\w+\b', corrected_text)
    checker.check_safety(words)


@arg('text', help='Text to check for safety')
@arg('--nsfw-words', help='File containing NSFW words')
@arg('--log-level', help='Set the logging level',
     choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
def check_text_safety(text: str, nsfw_words: str = None, log_level: str = 'WARNING'):
    """Check the safety of the given text."""
    from ally import main
    main.setup_logging(log_level)

    from text_corrector import TextCorrector

    corrector = TextCorrector()
    corrected_text = corrector.get_best_guess_sentence(text)
    words = re.findall(r'\b\w+\b', corrected_text.lower())

    checker = SafetyChecker(nsfw_words)
    result = checker.check_safety(words)

    print(f"Original text: {text}")
    print(f"Corrected text: {corrected_text}")
    print(f"Potential NSFW content: {result}")

if __name__ == "__main__":
    from ally import main
    main.run(check_text_safety)
