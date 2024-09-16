#!/usr/bin/env python3

"""
hello.py - An example Python module / script to say hello,
and ask the user how they are. We should always include a module-level
docstring to explain the purpose and basic usage of the program.

This script can be used as a module:
    from hello import hello
"""


import sys
import logging
import getpass
import textwrap

import argh
from argh import arg
import sh
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

from ally import main, terminal


__version__ = "1.0.0"

logger = logging.getLogger(__name__)


try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon")

sia = SentimentIntensityAnalyzer()


def analyze_sentiment(text):
    sentiment = sia.polarity_scores(text)
    if sentiment["compound"] > 0:
        return "Positive"
    elif sentiment["compound"] < 0:
        return "Negative"
    else:
        return "Neutral"


@arg("--name", help="name to be greeted")
@arg("--ai", help="use AI to respond")
@arg(
    "--model", help="specify which AI model", choices=["emmy", "claude", "dav", "clia"]
)
@arg(
    "--log-level",
    default="WARNING",
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    help="Set the logging level"
)
def hello(
    istream=sys.stdin,
    ostream=sys.stdout,
    name="World",
    ai=False,
    model="clia",
    log_level=None,
):
    """
    An example Unix-style Python module / script to say hello,
    and ask the user how they are.
    """
    main.setup_logging(log_level)


    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    if not name:
        name = getpass.getuser().title()

    print(f"Hello, {name}", file=ostream)
    print(f"How are you feeling?", file=ostream)

    if terminal.is_terminal(istream) and terminal.is_terminal(ostream):
        logger.debug("It's a terminal!")
        terminal.setup_history()
        feeling = terminal.input(": ").strip()
    else:
        feeling = istream.readline().strip()

    if feeling in ["", "lucky", "unlucky", "fortunate", "unfortunate"]:
        response = sh.fortune()
    elif ai:
        import llm

        prompt = f"Scenario: Your character asked 'How are you feeling?' and {name} said '{feeling.rstrip()}'. Please reply directly without any prelude, disclaimers or explanation."
        response = llm.query(prompt, model=model)
        response = response.strip().strip('"')
        response = textwrap.fill(response, width=80)
    else:
        sentiment = analyze_sentiment(feeling)
        logger.debug(f"{sentiment=}")
        if sentiment == "Positive":
            response = "I hope you have a great day!"
        elif sentiment == "Negative":
            response = "I hope you feel better soon."
        else:
            response = "Life has its ups and downs, hope yours swings up!"

    print(response, file=ostream)


if __name__ == "__main__":
    main.run(hello)
