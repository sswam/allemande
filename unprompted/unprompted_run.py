#!/usr/bin/env python3

import os
import sys
import logging
import argh
from lib_unprompted.shared import Unprompted

logger = logging.getLogger(__name__)

def process_unprompted(input_string):
    unprompted = Unprompted()
    unprompted.shortcode_user_vars = {}
    result = unprompted.start(input_string)
    unprompted.cleanup()
    unprompted.goodbye()
    return result

@argh.arg('--debug', help='enable debug logging')
@argh.arg('--verbose', help='enable verbose logging')
def main(*inp, debug=False, verbose=False):
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)

    os.chdir(script_dir)

    try:
        if len(inp):
            input_string = " ".join(inp)
        else:
            input_string = sys.stdin.read()

        output = process_unprompted(input_string)
        print(output)
    except Exception as e:
        logger.error(f"Error: %s %s", type(e).__name__, str(e))
        sys.exit(1)

if __name__ == '__main__':
    argh.dispatch_command(main)
