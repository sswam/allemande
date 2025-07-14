#!/usr/bin/env python3-allemande

"""
Strip stopwords from text input, outputting the filtered result.
"""

import string
import sys
from typing import TextIO

from nltk.corpus import stopwords  # type: ignore
import nltk  # type: ignore

from ally import main, logs  # type: ignore

logger = logs.get_logger()


stop_words = set()

stop_words_plus = set("""
find get give go let's look please search see show tell us me you they I want
need locate discover identify fetch display present explain describe ask query
what who where when why how can could would i'd like i'm looking for provide
retrieve generate compile summarize outline about on with without my your our
we information data details examples results article website page link list
image images picture pictures photo photos video videos chart graph map table
document pdf guide tutorial howto post thread study answer solution meaning
definition explanation comparison difference finding getting showing searching
kindly thanks cheers thank thankyou best top good easy simple quick fast free
cheap popular recommended is to do have i are there hi hello hey greetings
welcome g'day hiya howdy make
""".split())


def load_stopwords():
    """Ensure stopwords data is available, and load them."""
    global stop_words
    if stop_words:
        return
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords")
    stop_words = set(stopwords.words("english"))
    stop_words_plus.update(stop_words)


def strip_stopwords(text: str, strict: bool = False) -> str:
    """Remove stopwords from the given text."""
    load_stopwords()
    my_stop_words = stop_words_plus if strict else stop_words

    words = text.split()
    filtered_words = []
    for word in words:
        clean_word = word.strip(string.punctuation)
        if clean_word and clean_word.lower() not in my_stop_words:
            filtered_words.append(clean_word)

    return " ".join(filtered_words)


def process_stream(istream: TextIO, ostream: TextIO, strict: bool = False) -> None:
    """Process input stream, stripping stopwords, writing to output stream."""
    for line in istream:
        filtered = strip_stopwords(line.strip(), strict=strict)
        if filtered:
            ostream.write(f"{filtered}\n")


def setup_args(arg):
    """Set up command-line arguments."""
    arg("-s", "--strict", help="Strip additional common words", action="store_true")


if __name__ == "__main__":
    main.go(process_stream, setup_args)
