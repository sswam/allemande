#!/usr/bin/env python3

# typer.py: Simulate typing by reading from stdin and using xdotool to type each character.

import sys
import time
import random
import subprocess

import argh

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)


def typer(file=sys.stdin, mean_delay=0.2, sd_delay=0.4, min_delay=0.05, max_delay=1.5, mean_line_delay=10, sd_line_delay=50, min_line_delay=5, max_line_delay=30):
    """ Simulate typing by reading from stdin and using xdotool to type each character. """
    while True:
        char = file.read(1)
        if not char:
            break

        # Use xdotool to type each character
        delay = random.normalvariate(mean_delay, sd_delay)
        delay = clamp(delay, min_delay, max_delay)
        time.sleep(delay)
        if char == '\n':
            # Simulate 'Return' key press for newline characters
            # delay between 5 and 30 seconds.
            subprocess.run(['xdotool', 'key', '--clearmodifiers', 'Return'])
            delay = random.normalvariate(mean_line_delay, sd_line_delay)
            delay = clamp(delay, min_line_delay, max_line_delay)
            if delay < 5:
                delay = 5
            time.sleep(delay)
        elif char == ' ':
            # Simulate 'space' key press for spaces
            subprocess.run(['xdotool', 'key', '--clearmodifiers', 'space'])
        else:
            subprocess.run(['xdotool', 'type', char])

if __name__ == '__main__':
    argh.dispatch_command(typer)
