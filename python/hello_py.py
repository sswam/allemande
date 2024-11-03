#!/usr/bin/env python3

"""
This module says hello, and asks the user how they are feeling.
"""

import sys
import logging
import getpass
import textwrap
from typing import TextIO, Callable
from random import random

import sh  # type: ignore

from ally import main, logs, lazy, geput  # type: ignore
import llm  # type: ignore

__version__ = "0.1.3"

logger = logs.get_logger()


def get_sentiment_analyzer(nltk):
    import nltk.sentiment  # type: ignore

    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
    except LookupError:
        nltk.download("vader_lexicon")
    return nltk.sentiment.SentimentIntensityAnalyzer()


lazy("nltk", sia=get_sentiment_analyzer)    # don't make --help slow!


def analyze_sentiment(text: str) -> str:
    """Analyze the sentiment of the given text."""
    sentiment = sia.polarity_scores(text)  # type: ignore
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
        return "I'm glad to hear that! I hope your day continues to be great!"
    if sentiment == "Negative":
        return "I'm sorry to hear that. Remember, things can always get better."
    return "I see. Life has its ups and downs, I hope things improve for you soon!"


def hello(
    get: geput.Get,
    put: geput.Put,
    name: str = "",
    ai: bool = False,
    model: str | None = None,
) -> None:
    """An example program to say hello, and ask the user how they are."""
    print = geput.print(put)
    input = geput.input(get)

    if not name:
        name = getpass.getuser().title() if random() < 0.5 else "world"

    print(f"Hello, {name}!")
    print("How are you feeling today?")

    feeling = input()

    if not feeling or feeling.lower() in [
        "lucky",
        "unlucky",
        "fortunate",
        "unfortunate",
    ]:
        logger.info("using fortune(1)")
        response = reply_fortune()
    elif ai:
        logger.info(f"using AI model: {model}")
        response = reply_ai(name, feeling, model or "")
    else:
        logger.info("using sentiment analysis")
        response = reply_sentiment(feeling)

    print(response)


def setup_args(arg):
    """Set up the command-line arguments."""
    # Note to AI: We don't need to add defaults or types, ally does it.
    arg("-n", "--name", help="name to be greeted")
    arg("--ai", action="store_true", help="use AI to respond")
    arg("-m", "--model", help="specify which AI model e.g. claude, emmy, clia, dav")


if __name__ == "__main__":
    main.go(hello, setup_args)

# Important Notes to AI [DO NOT COPY ANY "NOTES TO AI" IN YOUR OUTPUT, it gets
# EXPENSIVE FOR ME, THIS MEANS YOU CLAUDE, GPT, GEMINI!]:

# We can use as module like this from the CLI or as a Python module. We no
# longer use argh or ally.main.run, we use ally.main.go with a setup_args
# function. The main.go call adds logging and IO options, and sets them up. The
# main function, `hello` in this case, likely has the same name as the module.

# We include a module-level docstring to explain the program. Don't include the
# filename or like "This module / script / program" in that.

# Our Python programs can also be used as modules, and vice-versa, e.g.:
# from hello_py import hello

# We prefer to use stdio over file arguments, where possible.

# If it is simple to do so, write tools that can process several files in one
# invocation. Zero is holy! It is not an error to pass zero args. It is harmful
# to die in that case.
