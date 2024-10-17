#!/usr/bin/env python3

"""
This module plays the game of 'Chinese whispers' by translating a given text
randomly among a set of languages multiple times.
"""

import sys
import logging
from typing import TextIO, Callable
from random import choice

from ally import main, logs, lazy, geput
import llm

__version__ = "0.1.2"

logger = logs.get_logger()

# Default list of languages to translate between
DEFAULT_LANGUAGES = [
    "English", "Spanish", "French", "German", "Italian", "Portuguese",
    "Russian", "Japanese", "Chinese", "Korean", "Arabic", "Hindi"
]


def translate(text: str, source_lang: str, target_lang: str, model: str) -> str:
    """Translate the given text from source language to target language."""
    prompt = (
        f"Please translate the following text from {source_lang} to {target_lang} with high accuracy. "
        f"Ensure that no information is lost or added during the translation process. "
        f"Please translate accurately into good quality writing in the target language. "
        f"The translation should sound natural not like a literal word-for-word translation."
        f"Maintain the original tone and context as closely as possible:\n\n"
        f'"{text}"\n\n'
        f"Provide only the translated text without any explanations or quotes."
    )
    response = llm.query(prompt, model=model)
    return response.strip()


def compare_translations(original: str, final: str, model: str) -> str:
    """Compare the original and final translations."""
    prompt = (
        f"Please compare the following two texts and describe similarities and differences. "
        f"Assign similarity scores out of 100% for meaning, tone, style, wording, and overall. "
        f"Original text: '{original}'\n"
        f"Final text: '{final}'\n"
        f"Provide your analysis and scores."
    )
    response = llm.query(prompt, model=model)
    return response.strip()


def whispers(
    get: geput.Get,
    put: geput.Put,
    text: str = "",
    iterations: int = 5,
    model: str = "default",
    languages: str = ",".join(DEFAULT_LANGUAGES),
    return_to_original: bool = True,
    source_lang: str = "English",
    compare: bool = False,
) -> None:
    """
    Play the game of 'Chinese whispers' by translating a given text
    randomly among a set of languages multiple times.
    """
    print = geput.print(put)
    input = geput.input(get)

    languages_list = languages.split(",")

    if not text:
        text = geput.whole(get)

    original_text = text
    current_lang = source_lang
    print(f"0. {current_lang}: {text}")

    if return_to_original:
        iterations -= 1

    if return_to_original and iterations < 1:
        raise ValueError("Number of iterations must be at least 1")

    for i in range(1, iterations + 1):
        excluded_languages = [current_lang]
        if return_to_original and i == iterations:
            excluded_languages.append(source_lang)
        possible_languages = [lang for lang in languages_list if lang not in excluded_languages]
        next_lang = choice(possible_languages)
        translated_text = translate(text, current_lang, next_lang, model)
        print(f"{i}. {next_lang}: {translated_text}")

        text = translated_text
        current_lang = next_lang

    if return_to_original:
        final_text = translate(text, current_lang, source_lang, model)
        print(f"{iterations+1}. {source_lang} (final): {final_text}")
    else:
        final_text = text

    logger.info(f"Completed {iterations + int(return_to_original)} translations using model: {model}")

    if compare:
        comparison = compare_translations(original_text, final_text, model)
        print("\nComparison of original and final texts:")
        print(comparison)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-t", "--text", help="initial text to translate")
    arg("-n", "--iterations", type=int, default=5, help="number of translations to perform")
    arg("-m", "--model", default="default", help="specify which AI model to use for translation")
    arg("-l", "--languages", default=",".join(DEFAULT_LANGUAGES), help="comma-separated list of languages to use")
    arg("-f", "--from", dest="source_lang", help="source language of the initial text")
    arg("--no-return", action="store_false", dest="return_to_original", help="disable returning to the original language")
    arg("-c", "--compare", action="store_true", help="compare original and final translations")


if __name__ == "__main__":
    main.go(whispers, setup_args)
