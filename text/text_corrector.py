#!/usr/bin/env python3

"""
text_corrector.py - A CLI tool to correct spelling and remove obfuscation from text.

This script can be used as a module:
    from text_corrector import correct_text
"""

import os
import re
import csv
import logging
from typing import List
from pathlib import Path
from collections import Counter

from spellchecker import SpellChecker
from nltk.metrics.distance import edit_distance
from argh import arg

from ally import main

__version__ = "1.0.0"

logger = main.get_logger()

class TextCorrector:
    def __init__(self):
        self.spell = SpellChecker()
        self.leet_map = {'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't'}
        self.word_list = set()
        self.word_freq = Counter()

        self._load_dictionaries()
        self._load_word_frequencies()

    def _load_dictionaries(self):
        for dict_file in ['/usr/share/dict/british-english', '/usr/share/dict/american-english']:
            with open(dict_file) as f:
                self.word_list.update(f.read().splitlines())
            self.word_list_lower = set(map(str.lower, self.word_list))

    def _load_word_frequencies(self):
        freq_file = Path(os.environ.get("ALLEMANDE_HOME", "")) / 'text' / 'word_freq.tsv'
        with open(freq_file, 'r', encoding='utf-8') as tsvfile:
            reader = csv.reader(tsvfile, delimiter='\t')
            for row in reader:
                if len(row) == 2:
                    word, count = row
                    self.word_freq[word.lower()] = int(count)

    def preprocess(self, text: str) -> str:
        return ''.join(self.leet_map.get(c, c) for c in text)

    def get_closest_word(self, word: str, max_distance: int = 2) -> str:
        word = word.lower()
        if word in self.word_list_lower:
            return word

        for distance in range(1, max_distance + 1):
            close_words = [w for w in self.word_list if edit_distance(word, w.lower()) == distance]
            if close_words:
                sorted_words = sorted(close_words, key=lambda x: self.word_freq.get(x.lower(), 0), reverse=True)
                logger.debug(f"Frequencies: {[(w, self.word_freq[w]) for w in sorted_words]}")
                return sorted_words[0]

        return f"[{word}]"

    def get_best_guess_sentence(self, text: str) -> str:
        text = self.preprocess(text)
        tokens = re.findall(r'\S+|\s+', text)
        words = [token for token in tokens if not token.isspace()]

        corrected_words = []
        for word_plus in words:
            logger.debug(f"{word_plus=}")

            match = re.match(r'^(\W*)([\w-]+)(\W*)$', word_plus)
            if match:
                leading, stripped_word, trailing = match.groups()
            else:
                leading, stripped_word, trailing = '', word_plus, ''

            word = stripped_word.lower()

            if self.spell.unknown([word]):
                word = self.spell.correction(word) or word
            logger.debug(f"spellchecked: {word=}")
            word = self.get_closest_word(word)
            logger.debug(f"closest: {word=}")

            if stripped_word.isupper():
                word = word.upper()
            elif stripped_word.istitle():
                word = word.capitalize()

            logger.debug(f"fixed case: {word=}")

            word_plus = f"{leading}{word}{trailing}"

            logger.debug(f"with leading and trailing: {word=}")

            corrected_words.append(word_plus)

        result = []
        word_index = 0
        for token in tokens:
            if token.isspace():
                result.append(token)
            else:
                result.append(corrected_words[word_index])
                word_index += 1

        return ''.join(result)

@arg("text", help="Text to correct")
def correct_text(text: str) -> str:
    """Correct spelling and remove obfuscation from the given text."""
    corrector = TextCorrector()
    return corrector.get_best_guess_sentence(text)

if __name__ == "__main__":
    main.run(correct_text)
