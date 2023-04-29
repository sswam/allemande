#!/usr/bin/env python3 
from collections import Counter
import re

def extract_ngrams(word, n):
    return [word[i:i+n] for i in range(len(word)-n+1)]

def build_ngram_frequency_data(word_list, n):
    ngram_counter = Counter()
    for word in word_list:
        ngrams = extract_ngrams(word, n)
        ngram_counter.update(ngrams)
    return ngram_counter

def is_pronounceable(word, ngram_frequencies, n, threshold):
    ngrams = extract_ngrams(word, n)
    word_score = 0
    for ngram in ngrams:
        word_score += ngram_frequencies[ngram]

    avg_score = word_score / len(ngrams)
    print(avg_score)
    return avg_score > threshold

def analyze_ngram_frequencies(ngram_frequencies):
    print(ngram_frequencies)
    total_count = sum(ngram_frequencies.values())
    ngram_count = len(ngram_frequencies)
    max_frequency = max(ngram_frequencies.values())
    min_frequency = min(ngram_frequencies.values())
    avg_frequency = total_count / ngram_count

    print(f"Total count of n-grams: {total_count}")
    print(f"Number of unique n-grams: {ngram_count}")
    print(f"Max frequency: {max_frequency}")
    print(f"Min frequency: {min_frequency}")
    print(f"Avg frequency: {avg_frequency}")

    return avg_frequency

def analyze():
    # Example usage with a larger word list and analysis
    with open("/usr/share/dict/words", "r") as file:
        # exclude all upper-case "words"
        word_list = [word.strip().lower() for word in file.readlines() if re.search(r"[a-z]", word) and not "'" in word]
        word_list = [word for word in word_list if re.match(r"^[a-z]+$", word)]
    
    n = 2  # Adjust n to capture the desired length of letter sequences
    ngram_frequencies = build_ngram_frequency_data(word_list, n)
    
    avg_frequency = analyze_ngram_frequencies(ngram_frequencies)


analyze()

## Example usage
#word_list = ['apple', 'banana', 'orange', 'grape', 'blueberry']  # Use a larger word list for better results
#n = 2  # Adjust n to capture the desired length of letter sequences
#ngram_frequencies = build_ngram_frequency_data(word_list, n)
#
#threshold = 1  # Adjust the threshold based on your dataset and desired sensitivity
#word = 'aardvark'  # Test word
#print(is_pronounceable(word, ngram_frequencies, n, threshold))  # Output: True
