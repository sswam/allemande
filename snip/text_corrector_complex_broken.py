import re
import logging
from typing import Dict, List, Tuple
from collections import defaultdict
from heapq import nlargest

from argh import arg
import nltk
from nltk.corpus import words as nltk_words
from nltk.corpus import brown as nltk_brown
from metaphone import doublemetaphone
from jellyfish import levenshtein_distance, jaro_winkler_similarity

class TextCorrector:
    # Define thresholds for good matches
    METAPHONE_THRESHOLD = 1  # Exact match for Metaphone
    JARO_WINKLER_THRESHOLD = 0.85  # High similarity for Jaro-Winkler
    LEVENSHTEIN_THRESHOLD = 0.8  # Relatively high similarity for Levenshtein

    def __init__(self, extra_words=None):
        global nltk_words
        try:
            nltk_words.words()
        except LookupError:
            logger.info("NLTK 'words' resource not found. Downloading now...")
            nltk.download('words')
            from nltk.corpus import words as nltk_words

        try:
            nltk_brown.words()
        except LookupError:
            logger.info("NLTK 'brown' resource not found. Downloading now...")
            nltk.download('brown')

        self.words_set = set(nltk_words.words())
        if extra_words:
            self.words_set = self.words_set.union(extra_words)
        self.leet_map = {'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't'}

        word_freq = nltk.FreqDist(nltk_brown.words())
        self.max_frequency = word_freq.most_common(1)[0][1]
        self.word_frequencies = {word: freq for word, freq in word_freq.items()}

        # Add n-gram models
        self.bigrams = nltk.bigrams(nltk_brown.words())
        self.bigram_freq = nltk.FreqDist(self.bigrams)
        self.trigrams = nltk.trigrams(nltk_brown.words())
        self.trigram_freq = nltk.FreqDist(self.trigrams)

    def match_unknown_words(self, text: str, metaphone_weight: float = 0.2,
                            jaro_winkler_weight: float = 0.4,
                            levenshtein_weight: float = 0.2,
                            frequency_weight: float = 0.2) -> Tuple[Dict[str, List[str]], List[str]]:
        words = re.findall(r'\b\w+\b', text)
        unknown_words = [word for word in words if word.lower() not in self.words_set]

        matched_words = {}
        unmatched_words = []

        for i, unknown in enumerate(unknown_words):
            context_words = self.get_context_words(unknown, i)  
            matches = self.find_matches(unknown, context_words)
            if matches:
                matched_words[unknown] = matches
            else:
                unmatched_words.append(unknown)

        return matched_words, unmatched_words

    def find_matches(self, unknown: str, context_words: List[str]) -> List[str]:
        metaphone_matches = []
        jaro_winkler_matches = []
        levenshtein_matches = []
        unknown_metaphone = doublemetaphone(unknown)[0]
        
        # Iterate through words in descending order of frequency
        for w in sorted(self.words_set, key=lambda x: self.word_frequencies.get(x, 0), reverse=True):
            if abs(len(w) - len(unknown)) <= 2:
                metaphone_sim = 1 if doublemetaphone(w)[0] == unknown_metaphone else 0
                jaro_winkler_sim = jaro_winkler_similarity(unknown, w)
                levenshtein_sim = 1 - (levenshtein_distance(unknown, w) / max(len(unknown), len(w)))

                context_score = self.calculate_context_score(w, context_words)
        
                # Only add matches that meet the threshold criteria
                if metaphone_sim >= self.METAPHONE_THRESHOLD:
                    metaphone_matches.append((w, metaphone_sim))
                if jaro_winkler_sim >= self.JARO_WINKLER_THRESHOLD:
                    jaro_winkler_matches.append((w, jaro_winkler_sim))
                if levenshtein_sim >= self.LEVENSHTEIN_THRESHOLD:
                    levenshtein_matches.append((w, levenshtein_sim))

            # Stop after finding enough good matches
            if len(metaphone_matches) >= 20 and len(jaro_winkler_matches) >= 20 and len(levenshtein_matches) >= 20:
                break

        combined_matches = set(w for w, _ in metaphone_matches + jaro_winkler_matches + levenshtein_matches)
        final_matches = []

        for w in combined_matches:
            metaphone_sim = next((sim for word, sim in metaphone_matches if word == w), 0)
            jaro_winkler_sim = next((sim for word, sim in jaro_winkler_matches if word == w), 0)
            levenshtein_sim = next((sim for word, sim in levenshtein_matches if word == w), 0)
            frequency_sim = self.word_frequencies.get(w, 0) / self.max_frequency
            context_score = self.calculate_context_score(w, context_words)

            similarity = (
                metaphone_sim * 0.2 +
                jaro_winkler_sim * 0.4 +
                levenshtein_sim * 0.2 +
                frequency_sim * 0.2 +
                context_score * 0.2
            )

            final_matches.append((w, similarity))

        final_matches.sort(key=lambda x: (-x[1], x[0]))
        return [match[0] for match in final_matches[:5]]

    def get_context_words(self, words, index, window=2):
        start = max(0, index - window)
        end = min(len(words), index + window + 1)
        return words[start:index] + words[index+1:end]

    def calculate_context_score(self, word, context_words):
        score = 0
        for i, context_word in enumerate(context_words):
            if i == 0:
                score += self.bigram_freq[(context_word, word)] / self.max_frequency
            elif i == len(context_words) - 1:
                score += self.bigram_freq[(word, context_word)] / self.max_frequency
            else:
                score += self.trigram_freq[(context_words[i-1], word, context_word)] / self.max_frequency
        return score / len(context_words) if context_words else 0

    def preprocess(self, text: str) -> str:
        return ''.join(self.leet_map.get(c, c) for c in text.lower())


    def get_best_guess_sentence(self, text: str) -> str:
        text = self.preprocess(text)

        # Split the text into words, preserving punctuation and spaces
        tokens = re.findall(r'\S+|\s+', text)

        # Process only non-space tokens
        words = [token for token in tokens if not token.isspace()]

        matched_words, _ = self.match_unknown_words(text)

        corrected_words = []
        for word in words:
            # Strip punctuation for matching, but keep track of it
            stripped_word = word.strip('.,!?:;()[]{}""''')
            lower_word = stripped_word.lower()

            if lower_word in matched_words:
                corrected = matched_words[lower_word][0]

                # Preserve original capitalization
                if stripped_word.isupper():
                    corrected = corrected.upper()
                elif stripped_word.istitle():
                    corrected = corrected.capitalize()

                # Reattach any stripped punctuation
                corrected = word.replace(stripped_word, corrected)
            else:
                corrected = word

            corrected_words.append(corrected)

        # Reconstruct the sentence with original spacing
        result = []
        word_index = 0
        for token in tokens:
            if token.isspace():
                result.append(token)
            else:
                result.append(corrected_words[word_index])
                word_index += 1

        return ''.join(result)


@arg('text', help='Text to correct')
def correct_text(text: str):
    """Correct spelling and remove obfuscation from the given text."""
    corrector = TextCorrector()
    corrected_text = corrector.get_best_guess_sentence(text)
    print(f"Original text: {text}")
    print(f"Corrected text: {corrected_text}")


if __name__ == "__main__":
    from ally import main
    main.run(correct_text)

