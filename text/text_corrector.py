#!/usr/bin/env python3-allemande

"""
text_corrector.py - A CLI tool to correct spelling and remove obfuscation from text.

This script can be used as a module:
    from text_corrector import correct_text
"""

import os
import re
import csv
import logging
from typing import List, Tuple
from pathlib import Path
from collections import Counter
import time
import pickle

from spellchecker import SpellChecker
from argh import arg

from ally import main
from bk_tree import BKTree

__version__ = "1.1.0"

logger = main.get_logger()


class TextCorrector:
    def __init__(self):
        self.spell = SpellChecker()
        self.leet_map = {'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't'}
        self.word_list = set()
        self.word_freq = Counter()
        self.word_case = {}
        self.bk_tree = BKTree()

        self._load_dictionaries()
        self._load_word_frequencies()

    def _load_dictionaries(self):
        pickle_file = main.resource('text/dictionaries.pkl')
        try:
            with open(pickle_file, 'rb') as f:
                self.word_list, self.bk_tree, self.word_case = pickle.load(f)
            return
        except FileNotFoundError:
            pass

        for dict_file in ['/usr/share/dict/british-english', '/usr/share/dict/american-english']:
            with open(dict_file) as f:
                self.word_list.update(f.read().splitlines())

        for word in self.word_list:
            word_lc = word.lower()
            self.bk_tree.add(word_lc)
            if word_lc != word:
                self.word_case[word_lc] = word

        with open(pickle_file, 'wb') as f:
            pickle.dump((self.word_list, self.bk_tree, self.word_case), f)

    def _load_word_frequencies(self):
        freq_file = main.resource('text/word_freq.tsv')
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
        if word in self.word_list or word in self.word_case:
            return word

        close_words = self.bk_tree.search(word, max_distance)
        if close_words:
            sorted_words = sorted(close_words, key=lambda x: self.word_freq.get(x[0].lower(), 0), reverse=True)
            logger.debug(f"Frequencies: {[(w, self.word_freq[w[0]]) for w in sorted_words]}")
            closest = sorted_words[0][0]
            return self.word_case.get(closest, closest)

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
