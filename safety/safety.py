#!/usr/bin/env python3-allemande

"""
Process text and data structures, optionally filtering or enabling adult content.
"""

import re
import json
from typing import Any
from pathlib import Path
from io import TextIOBase
from inflect import engine

from ally import main, logs, filer  # type: ignore

__version__ = "0.1.3"

logger = logs.get_logger()

NSFW_WORDS: list[str] = []
NSFW_WORDS_RE, NSFW_PHRASE_RE = "", ""
REMOVE_NSFW_SECTIONS_RE, REMOVE_NSFW_PHRASES_RE, REMOVE_NSFW_LINES_RE = "", "", ""

inflection = engine()


def get_plural_and_singular_forms(word_or_phrase: str) -> list[str]:
    """
    Get the singular and plural forms of a word or phrase.
    This won't work well for non-English words.
    I could try using AI to make the lists.
    """
    variants = {word_or_phrase}
    try:
        plural = inflection.plural(word_or_phrase)
        if plural:
            variants.add(plural)
    except Exception as e:  # pylint: disable=broad-except
        logger.debug("Plural error for %s: %s", word_or_phrase, e)
    try:
        singular = inflection.singular_noun(word_or_phrase)
        if singular:
            variants.add(singular)
    except Exception as e:  # pylint: disable=broad-except
        logger.debug("Singular error for %s: %s", word_or_phrase, e)

    # exclude bogus "ss" ending plural forms
    variants = {variant for variant in variants if not variant.endswith("ss")}

    return list(variants)


def compile_regexps(nsfw_words: list[str]) -> tuple[str, str]:
    """Compile regular expressions for NSFW words and phrases."""
    nsfw_word_re = "|".join(re.escape(word) for word in nsfw_words)
    any_word_re = r"\b(\w+)\b\s*"
    phrase_or_empty_re = rf"(?:{any_word_re})*"
    nsfw_phrase_re = rf"{phrase_or_empty_re}(?:{nsfw_word_re}){phrase_or_empty_re}"
    return nsfw_word_re, nsfw_phrase_re


def load_nsfw_words(files: list[Path]) -> list[str]:
    """Load NSFW words from plain text files, one word or phrase per line."""
    nsfw_words: list[str] = []
    for file in files:
        logger.debug("Loading file: %s", file)
        with file.open() as f:
            nsfw_words.extend(line.strip() for line in f if line)

    # add plural and singular forms of each word
    nsfw_words = [variant for word in nsfw_words for variant in get_plural_and_singular_forms(word)]

    # deduplicate
    nsfw_words = list(set(nsfw_words))

    # sort descending by length to match longer phrases first
    nsfw_words.sort(key=len, reverse=True)

    return nsfw_words


def safety_setup():
    """Set up safety module."""
    global NSFW_WORDS, NSFW_WORDS_RE, NSFW_PHRASE_RE, REMOVE_NSFW_SECTIONS_RE, REMOVE_NSFW_PHRASES_RE, REMOVE_NSFW_LINES_RE  # pylint: disable=global-statement

    NSFW_WORDS_FILES_SHUTTERSTOCK = [
        path
        for path in list(filer.resource("safety/nsfw_words").glob("*"))
        if path.is_file() and not path.name.startswith(".") and not path.name.endswith(".md") and path.name != "LICENSE"
    ]

    NSFW_WORDS_FILES_EXTRA = [filer.resource("safety/nsfw_words_extra.txt")]

    NSFW_WORDS_FILES = NSFW_WORDS_FILES_EXTRA + NSFW_WORDS_FILES_SHUTTERSTOCK

    NSFW_WORDS = load_nsfw_words(NSFW_WORDS_FILES)
    NSFW_WORDS_RE, NSFW_PHRASE_RE = compile_regexps(NSFW_WORDS)

    REMOVE_NSFW_SECTIONS_RE = r"""(?mix)
        ^                  # Start of line
        \#+\s*             # Heading marker and optional whitespace
        .*?                # Any characters (non-greedy)
        NSFW[.\n]*?        # 'NSFW' followed by any text including newlines
        (\n\n|(?=^\#+|\Z)) # Double newline OR next heading or end
        """

    REMOVE_NSFW_PHRASES_RE = r"""(?ix)
        (
            ({NSFW_PHRASE_RE})\s*,\s* |
            ,\s*({NSFW_PHRASE_RE}) |
            ({NSFW_PHRASE_RE})\s+and |
            and\s+({NSFW_PHRASE_RE})
        )
        """

    REMOVE_NSFW_LINES_RE = r"""(?mix)
        ^.*?\b({NSFW_WORDS_RE})\b.*\n
        """


def apply_or_remove_adult_options(data: Any, adult: bool) -> Any:
    """Apply adult options, recursively modifying the data structure.

    If adult is False, removes adult content. If True, applies adult content
    by moving *_adult values to their base keys.
    """
    adult_suffix = "_adult"
    adult_suffix_len = len(adult_suffix)

    if data is None or isinstance(data, (int, float, bool)) or callable(data):
        pass
    elif isinstance(data, dict):
        for k, v in list(data.items()):
            if k.endswith(adult_suffix):
                base_key = k[:-adult_suffix_len]
                if adult:
                    data[base_key] = v
                del data[k]

            data[k] = apply_or_remove_adult_options(v, adult)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            data[i] = apply_or_remove_adult_options(v, adult)
        data = [v for v in data if v]
    elif isinstance(data, str):
        if not adult:
            data = remove_nsfw_text(data)
    else:
        logger.warning("Unexpected data type, not checked: %s", type(data))

    return data


def remove_nsfw_text(text: str) -> str:
    """Remove adult/NSFW content from text."""
    # Remove whole sections beginning with a heading containing "NSFW"
    text = re.sub(REMOVE_NSFW_SECTIONS_RE, "", text)

    # Remove NSFW phrases from lists (with commas or 'and')
    text = re.sub(REMOVE_NSFW_PHRASES_RE, "", text)

    # Remove any remaining lines containing NSFW words
    text = re.sub(REMOVE_NSFW_LINES_RE, "", text)

    return text


def process(istream: TextIOBase, ostream: TextIOBase, adult: bool = False, is_json: bool = False) -> None:
    """Process input data, applying adult content filtering as specified."""
    safety_setup()

    if is_json:
        data = json.load(istream)  # type: ignore
    else:
        data = {"text": istream.read()}

    data = apply_or_remove_adult_options(data, adult)

    if is_json:
        json.dump(data, ostream, indent=2)  # type: ignore
        ostream.write("\n")
    else:
        ostream.write(data["text"])
        if not data["text"].endswith("\n"):
            ostream.write("\n")


def setup_args(arg):
    """Set up command-line arguments."""
    arg("-a", "--adult", action="store_true", help="enable adult content")
    arg("-j", "--json", action="store_true", dest="is_json", help="expect JSON input")


if __name__ == "__main__":
    main.go(process, setup_args)
else:
    safety_setup()
