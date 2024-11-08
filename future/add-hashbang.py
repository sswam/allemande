#!/usr/bin/env python3-allemande

# add-hashbang.py: add hashbangs lines to files that don't have them.

# This script takes a list of files as arguments and adds a hashbang to the top
# of each file. If the file already has a hashbang, it will not be modified. It
# guesses the hashbang based on the file extension. There is an option to use
# OpenAI GPT API to guess the hashbang based on the file contents when
# necessary, if enabled.

import argparse
import os
import re
import shutil
import sys

# The hashbangs to use for different file extensions.
EXT_HASHBANGS = {
    '.py': '#!/usr/bin/env python3',
    '.sh': '#!/bin/bash',
    '.pl': '#!/usr/bin/env perl',
}

# The hashbang to use if no other hashbang is found.
DEFAULT_HASHBANG = '#!/bin/bash'

# The maximum amount of bytes to read from a file when guessing the hashbang.
MAX_BYTES = 1024

# The regular expression to use when guessing the hashbang of a file.
RE_HASHBANG = re.compile(r'^#!\s*(\S+)(\s+(.*))?\s*$')

def has_hashbang(file_head):
    return re.match(RE_HASHBANG, file_head)

def guess_hashbang_by_extension(path):
    """ Guess the hashbang of a file based on its extension. """
    _, ext = os.path.splitext(path)
    if ext
    return EXT_HASHBANGS.get(ext, DEFAULT_HASHBANG)

    """Guess the hashbang of a file based on its extension or contents.

    Arguments:
        path: The path to the file to guess the hashbang of.

    Returns:
        A hashbang string.
    """
    # Guess the
