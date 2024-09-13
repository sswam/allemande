#!/usr/bin/env python3

"""
Sync subtitles with a script file.
"""


import sys
import logging
import difflib
from pathlib import Path

import nltk
from nltk.tokenize import word_tokenize
from nltk.metrics.distance import edit_distance
import argh
import colorama
from colorama import Fore, Style



colorama.init()


try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')


def fuzzy_match(subtitle, script_chunk, threshold=0.6):
    """
    Perform fuzzy matching between subtitle and script chunk.

    Args:
        subtitle (str): The subtitle text to match.
        script_chunk (str): A chunk of the script to search in.
        threshold (float): The similarity threshold for matching.

    Returns:
        tuple: A tuple containing (start_pos, end_pos) of the match in the script chunk,
               or (-1, -1) if no match is found.
    """
    # Tokenize subtitle and script chunk
    subtitle_tokens = word_tokenize(subtitle.lower())
    script_tokens = word_tokenize(script_chunk.lower())

    best_match_score = 0
    best_match_index = -1

    # Sliding window approach
    for i in range(len(script_tokens) - len(subtitle_tokens) + 1):
        window = script_tokens[i:i+len(subtitle_tokens)]

        # Calculate similarity using Levenshtein distance
        similarity = 1 - edit_distance(subtitle_tokens, window) / max(len(subtitle_tokens), len(window))

        if similarity > best_match_score and similarity >= threshold:
            best_match_score = similarity
            best_match_index = i

    if best_match_index != -1:
        # Find the character positions corresponding to the token indices
        start_pos = find_char_position(script_chunk, script_tokens, best_match_index)
        end_pos = find_char_position(script_chunk, script_tokens, best_match_index + len(subtitle_tokens))
        return (start_pos, end_pos)

    return (-1, -1)


def find_char_position(text, tokens, token_index):
    """
    Find the character position in the original text corresponding to a token index.
    """
    char_index = 0
    for i, token in enumerate(tokens):
        if i == token_index:
            return char_index
        # Find the next occurrence of the token in the text
        token_start = text.lower().find(token, char_index)
        if token_start == -1:
            # If token not found, move to the next non-space character
            char_index = next((j for j in range(char_index, len(text)) if not text[j].isspace()), len(text))
        else:
            char_index = token_start + len(token)
    return len(text)  # Return end of text if token_index is beyond the last token


last_message_length = 0


def print_ephemeral(message, color=Fore.BLUE):
    global last_message_length
    # Clear previous message
    sys.stderr.write('\b' * last_message_length + ' ' * last_message_length + '\b' * last_message_length)
    if message:
        sys.stderr.write(f"{color}{message}{Style.RESET_ALL}")
    sys.stderr.flush()
    last_message_length = len(message)


def process_subtitles(script_file, look_ahead=2000, threshold=0.6, min_match_length=10, whole_lines=False):
    """
    Process subtitles from stdin and sync with the script.

    Args:
        script_file (str): Path to the script file.
        look_ahead (int): Number of characters to look ahead in the script.
        threshold (float): The similarity threshold for matching.
    """
    with open(script_file, 'r') as f:
        script = f.read()

    script_pos = 0

    for subtitle in sys.stdin:
        subtitle = subtitle.strip()
        if not subtitle:
            continue
        if len(subtitle) < min_match_length:
            continue

        chunk_end = min(script_pos + look_ahead, len(script))
        script_chunk = script[script_pos:chunk_end]

        _match_pos, match_end = fuzzy_match(subtitle, script_chunk, threshold)
        if match_end != -1:
            print_ephemeral('')
            match_end += script_pos
            if whole_lines:
                next_newline = script.find('\n', match_end)
                if next_newline != -1:
                    match_end = next_newline + 1
            print(script[script_pos:match_end], end="")
            sys.stdout.flush()
            script_pos = match_end
        else:
            print_ephemeral(f"? {subtitle}")

    print_ephemeral('')


@argh.arg('script_file', help='Path to the script file')
@argh.arg('--look-ahead', help='Number of characters to look ahead in the script', type=int, default=2000)
@argh.arg('--threshold', help='Similarity threshold for fuzzy matching', type=float, default=0.6)
@argh.arg('--min-match-length', help='Minimum subtitle char-length to try to match the script', type=int, default=10)
@argh.arg('--lines', help='Output the whole line in advance when matching', action='store_true')
@argh.arg('--debug', help='Enable debug logging', action='store_const', const=logging.DEBUG, dest='log_level')
@argh.arg('--verbose', help='Enable verbose logging', action='store_const', const=logging.INFO, dest='log_level')
def main(script_file, look_ahead=2000, threshold=0.6, min_match_length=10, lines=False, log_level=logging.WARNING):
    """
    Sync subtitles with a script file.

    This script reads subtitles from stdin and writes the synchronized script to stdout.

    Usage:
        python script_sync.py SCRIPT_FILE [--look-ahead LOOK_AHEAD] [--threshold THRESHOLD] [--lines] [--debug] [--verbose]
    """

    global logger
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)

    if not Path(script_file).is_file():
        logger.error(f"Script file not found: {script_file}")
        sys.exit(1)

    try:
        process_subtitles(script_file, look_ahead, threshold, min_match_length, whole_lines=lines)
    except Exception as e:
        logger.error(f"Error: {type(e).__name__} - {str(e)}")
        if log_level == logging.DEBUG:
            raise
        sys.exit(1)



if __name__ == '__main__':
    argh.dispatch_command(main)
