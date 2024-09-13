#!/usr/bin/env python3

# Here's a simple Python program that determines the language of a file based on its extension, following the style of the provided hello.py:

import os
import sys
import logging
import argh

__version__ = "1.0.0"

logger = logging.getLogger(__name__)

def get_language(filename):
    """
    Determine the language of a file based on its extension.

    Args:
        filename (str): The name of the file.

    Returns:
        str: The determined language.
    """
    extension = os.path.splitext(filename)[1].lower()

    language_map = {
        '.py': 'python',
        '.sh': 'bash',
        '.pl': 'perl',
        '.js': 'javascript',
        '.java': 'java',
        '.cpp': 'c++',
        '.c': 'c',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.php': 'php',
        '.html': 'html',
        '.css': 'css',
    }

    return language_map.get(extension, 'bash' if not extension else 'unknown')

@argh.arg('filename', help='filename to determine language')
@argh.arg('--debug', help='enable debug logging', action='store_const', const=logging.DEBUG, dest='log_level')
def main(filename, log_level=logging.WARNING):
    """
    Determine the language of a file based on its extension.

    Usage:
        python script.py <filename> [--debug]
    """
    logging.basicConfig(level=log_level, format="%(message)s")

    try:
        return get_language(filename)
    except Exception as e:
        logger.error("Error: %s %s", type(e).__name__, str(e))
        if log_level == logging.DEBUG:
            raise
        sys.exit(1)

if __name__ == '__main__':
    argh.dispatch_command(main)
