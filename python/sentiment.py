#!/usr/bin/env python

import sys

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer


try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()


def analyze_sentiment(text):
    sentiment = sia.polarity_scores(text)
    if sentiment['compound'] > 0:
        return 'Positive'
    elif sentiment['compound'] < 0:
        return 'Negative'
    else:
        return 'Neutral'


for text in sys.stdin:
    print(analyze_sentiment(text))
