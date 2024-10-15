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

from ally import main, logs, lazy, Get, Put  # type: ignore
import llm  # type: ignore

__version__ = "0.1.2"

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
    get: Get,
    put: Put,
    name: str = "",
    ai: bool = False,
    model: str | None = None,
) -> None:
    """
    An example module / script to say hello,
    and ask the user how they are.
    """
    if not name:
        name = getpass.getuser().title() if random() < 0.5 else "world"

    put(f"Hello, {name}!")
    put("How are you feeling today?")

    feeling = get()

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

    put(response)


def setup_args(arg):
    """Set up the command-line arguments."""
    # Note to AI (do not copy): We don't need to add defaults or types, ally does it.
    arg("-n", "--name", help="name to be greeted")
    arg("--ai", action="store_true", help="use AI to respond")
    arg("-m", "--model", help="specify which AI model e.g. claude, emmy, clia, dav")


if __name__ == "__main__":
    main.go(hello, setup_args)

"""
Important Notes for AI [DO NOT COPY THEM IN YOUR OUTPUT, it gets EXPENSIVE FOR ME!]:

We can use as module like this from the CLI or as a Python module. We no longer
use argh or ally.main.run, we use ally.main.go with a setup_args function.
The main.go call adds logging and IO options, and sets them up.
The main function, `hello` in this case, likely has the same name as the module.

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

Double line breaks are used to separate top-level functions and classes.

Our scripts default to stdio.

In modern Python, we can use types like list[str] rather than List[str], same for dict, set, etc.

Our scripts can also be used as modules, and vice-versa.
    from hello import hello

Stdout is only for normal output. Use logging for info, warning or error messages.

None is different from 0. Don't "simplify" `if foo is None: foo = default` to `foo = foo or default`.

The original coder was probably not an idiot. Be careful when "fixing" things.
We use at least Python 3.10, normally 3.12 or the latest stable version. Please use new features as needed.
For example, use modern type hints such as list[str]|None rather than Optional[List[str]]
"""
