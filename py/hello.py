#!/usr/bin/env python

# Says Hello, world

import sys
import getpass
import textwrap
from random import random
import sh
import llm
import nltk.sentiment

__version__ = "0.1.0"

nltk.download("vader_lexicon", quiet=True)
sia = nltk.sentiment.SentimentIntensityAnalyzer()

print(f"Hello, {getpass.getuser().title() if random() < 0.5 else 'world'}")
print("How are you feeling?")

feeling = input().strip()

if feeling in ["", "lucky", "unlucky", "fortunate", "unfortunate"]:
    response = sh.fortune().strip()
elif "--ai" in sys.argv:
    model = next((arg.split("=")[1] for arg in sys.argv if arg.startswith("--model=")), None)
    prompt = f"Scenario: Your character asked 'How are you feeling?' and {getpass.getuser().title()} said '{feeling}'. Please reply directly without any prelude, disclaimers or explanation."
    response = textwrap.fill(llm.query(prompt, model=model).strip().strip('"'), width=80)
else:
    sentiment = sia.polarity_scores(feeling)["compound"]
    response = "I hope you have a great day!" if sentiment > 0 else "I hope you feel better soon." if sentiment < 0 else "Life has its ups and downs, hope yours swings up!"

print(response)

if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
    print("\nI see you also offered me some files, but I'm not interested in them.")
    print("This is just a simple hello script!")
