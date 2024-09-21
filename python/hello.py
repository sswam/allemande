#!/usr/bin/env python3

"""
hello.py - An example Python module / script to say hello,
and ask the user how they are.
"""

import sys
import logging
import getpass
import textwrap
from typing import TextIO, Optional
from random import random

from argh import arg
import sh
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

from ally import main

__version__ = "0.1.0"

logger = main.get_logger()

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon")

sia = SentimentIntensityAnalyzer()


def analyze_sentiment(text: str) -> str:
    """Analyze the sentiment of the given text."""
    sentiment = sia.polarity_scores(text)
    if sentiment["compound"] > 0:
        return "Positive"
    if sentiment["compound"] < 0:
        return "Negative"
    return "Neutral"


def reply_fortune() -> str:
    """Return a fortune cookie message."""
    return sh.fortune().strip()


def reply_ai(name: str, feeling: str, model: str) -> str:
    """Generate an AI response based on the user's feeling."""
    import llm  # slow to load, so don't load unless needed

    prompt = (
        f"Scenario: Your character asked 'How are you feeling?' "
        f"and {name} said '{feeling.rstrip()}'. "
        f"Please reply directly without any prelude, disclaimers or explanation."
    )
    response = llm.query(prompt, model=model)
    response = response.strip().strip('"')
    response = textwrap.fill(response, width=80)
    return response


def reply_sentiment(feeling: str) -> str:
    """Generate a response based on sentiment analysis of the user's feeling."""
    sentiment = analyze_sentiment(feeling)
    logger.debug(f"{sentiment=}")
    if sentiment == "Positive":
        return "I hope you have a great day!"
    if sentiment == "Negative":
        return "I hope you feel better soon."
    return "Life has its ups and downs, hope yours swings up!"


@arg("--name", help="name to be greeted")
@arg("--ai", help="use AI to respond")
@arg(
    "--model",
    choices=["emmy", "claude", "dav", "clia"],
    metavar="MODEL",
    help="specify which AI model {emma,claude,dav,clia}",
)
def hello(
    input: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    name: str = "",
    ai: bool = False,
    model: str = None,
) -> None:
    """
    An example module / script to say hello,
    and ask the user how they are.
    """
    if not name:
        name = getpass.getuser().title() if random() < 0.5 else "world"

    get, put = main.io(input, output)

    put(f"Hello, {name}")
    put("How are you feeling?")

    feeling = get()

    if feeling in ["", "lucky", "unlucky", "fortunate", "unfortunate"]:
        logger.info("using fortune(1)")
        response = reply_fortune()
    elif ai:
        logger.info("using AI model")
        response = reply_ai(name, feeling, model)
    else:
        logger.info("using sentiment analysis")
        response = reply_sentiment(feeling)

    put(response)


if __name__ == "__main__":
    main.run(hello)

"""
Important Notes for AI:

AVOID DEEP INDENTATON OR NESTING, it's better to use if/elif or a function.
If needed, we can use variables to avoid repeating parts of conditions.
This is the number one rule!

In most cases for error handling we just allow the script to exit by not
catching the exception. This is a deliberate choice.

We raise exceptions rather that printing to stderr then exiting. Never handle
something that should be an exception as a warning.

We should always include a module-level docstring to explain the program.
Don't include the filename in that.

If sensible and simple to do so, write tools that can process several files in one invocation.  # XXX not sure
Zero is holy! It is not an error to pass zero files to process. Just naturally do nothing in that case.

Double line breaks are used to separate top-level functions and classes.

I know it's naughty to use 'input' as a variable name, but let's do it anyway.

Our scripts default to stdio.

There is magic in ally.main to open files and print exceptions nicely.

Our scripts can also be used as modules, and vice-versa.
    from hello import hello

When writing other scripts based on this one, please do not include these notes!
"""
