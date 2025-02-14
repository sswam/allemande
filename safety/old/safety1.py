# safety.py:

import re
import nltk
from nltk.corpus import words as nltk_words

# Try to access the words corpus, download if not available
try:
    nltk_words.words()
except LookupError:
    print("NLTK 'words' resource not found. Downloading now...")
    nltk.download('words')
    from nltk.corpus import words as nltk_words

def preprocess(text):
    leet_map = {'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't'}
    return ''.join(leet_map.get(c, c) for c in text.lower())

def soundex(word):
    codes = {'bfpv': '1', 'cgjkqsxz': '2', 'dt': '3', 'l': '4', 'mn': '5', 'r': '6'}
    word = word.lower()
    coded = word[0]
    for char in word[1:]:
        for k, v in codes.items():
            if char in k:
                coded += v
                break
        else:
            coded += '0'
    coded = coded.replace('0', '')
    return (coded + '000')[:4]

def match_unknown_words(text):
    words_set = set(nltk_words.words())
    unknown_words = []
    for word in re.findall(r'\b\w+\b', preprocess(text)):
        if word not in words_set:
            unknown_words.append(word)

    matched_words = {}
    for unknown in unknown_words:
        unknown_soundex = soundex(unknown)
        matches = [w for w in words_set if soundex(w) == unknown_soundex]
        matched_words[unknown] = matches[:5]

    return matched_words

# Example usage
if __name__ == "__main__":
    text = "Th1s is a t3st w1th s0m3 l33t sp34k elephnt"
    print(match_unknown_words(text))


# TODO, when I run this it gives: {'elephnt': ['elvanite', 'elephantiac', 'elevener', 'eleventhly', 'elfinwood']}
# I would expect it to include 'elephant'. Also, does it sort with better matches first.
