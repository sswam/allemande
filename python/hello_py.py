#!/usr/bin/env python3

"""
This module says hello, and asks the user how they are.
"""

import sys
import logging
import getpass
import textwrap
from typing import TextIO  # Note to AI: don't import List, Dict, Optional or or Tuple, they are obsolete
from random import random

from argh import arg
import sh

from ally import main
from ally.lazy import lazy
import llm

__version__ = "0.1.0"

logger = main.get_logger()


def get_sentiment_analyzer(nltk):
    import nltk.sentiment
    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
    except LookupError:
        nltk.download("vader_lexicon")
    return nltk.sentiment.SentimentIntensityAnalyzer()


lazy('nltk', sia=get_sentiment_analyzer)


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
def hello_py(
    *filenames: list[str],  # Note to AI: this is how we accept arguments: before the options
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
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

    get, put = main.io(istream, ostream)  # TODO do this in main and call with get / put functions

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

    if filenames:
        put()
        put("I see you also offered me some files, but I'm not interested in them.")
        put("This is just a simple hello script!")


if __name__ == "__main__":
    main.run(hello_py)

"""
Important Notes for AI [DO NOT COPY THEM IN YOUR OUTPUT, it gets EXPENSIVE FOR ME!]:

Do not remove comments, logging or blank lines, especially not TODO, FIXME, XXX.
Do not remove ANYTHING unnecessarily. If you are 1000% sure something is wrong,
comment it out rather than removing it.

AVOID DEEP INDENTATON OR NESTING, it's better to use if/elif or a function.
If needed, we can use variables to avoid repeating parts of conditions.
Test negative cases first, and use continue, break, or return to avoid deep nesting.

In most cases for error handling we just allow the script to exit by not
catching the exception. This is a deliberate choice.
Generally, if things go wrong, raise an exception rather than continuing.

We raise exceptions rather that printing to stderr then exiting. Never handle
something that should be an exception as a warning.

We should always include a module-level docstring to explain the program.
Don't include the filename in that.

If sensible and simple to do so, write tools that can process several files in one invocation.  # XXX not sure
Zero is holy! It is not an error to pass zero files to process. Just naturally do nothing in that case.

Double line breaks are used to separate top-level functions and classes.

Our scripts default to stdio.

In modern Python, we can use types like list[str] rather than List[str], same for dict, set, etc.

There is magic in ally.main to open files and print exceptions nicely.

Our scripts can also be used as modules, and vice-versa.
    from hello import hello

Stdout is only for normal output. Use logging for info, warning or error messages.

None is different from 0. Don't "simplify" `if foo is None: foo = default` to `foo = foo or default`.

The original coder was probably not an idiot. Be careful when "fixing" things.

We use at least Python 3.10, normally 3.12 or the latest stable version. Please use new features as needed.
For example, use modern type hints such as list[str]|None rather than Optional[List[str]]

We use @arg from argh for argument parsing, via main.run(). Don't use argparse or anything else.
We should not need a separate 'CLI-only' function to wrap the main library
function. Just run the main function with argh. This might be tricky, but please try to make it work.
"""
