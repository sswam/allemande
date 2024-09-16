#!/usr/bin/env python3

"""
Highlight matches in different colors.
"""

import sys
import re
from colorama import init, Fore, Style
import argh

init(autoreset=True)

def color_text(text, color):
    color_map = {
        'red': Fore.RED,
        'green': Fore.GREEN,
        'blue': Fore.BLUE,
        'yellow': Fore.YELLOW,
        'magenta': Fore.MAGENTA,
        'cyan': Fore.CYAN,
    }
    return f"{color_map.get(color.lower(), '')}{text}{Style.RESET_ALL}"

def highlight(patterns, colors, word_regexp):
    for line in sys.stdin:
        output_line = line
        matches = []

        # Find all matches for all patterns
        for i, pattern in enumerate(patterns):
            if word_regexp:
                pattern = r'\b(' + pattern + r')\b'
            matches.extend((m.start(), m.end(), i) for m in re.finditer(pattern, line))

        # Sort matches by start position
        matches.sort(key=lambda x: x[0])

        # Apply coloring
        if matches:
            new_line = []
            last_end = 0
            for start, end, i in matches:
                new_line.append(output_line[last_end:start])
                color = colors[i]
                new_line.append(color_text(output_line[start:end], color))
                last_end = end
            new_line.append(output_line[last_end:])
            output_line = ''.join(new_line)

        sys.stdout.write(output_line)

@argh.arg('patterns', nargs='*', help="Patterns to search for and their colors")
@argh.arg('-w', '--word-regexp', help="Match whole words only")
def main(patterns, word_regexp=False):
    """
    Highlight matches in different colors.

    Supported colors are:
      red, green, blue, yellow, magenta, cyan

    Examples:
      highlight.py 'blo*d' red 'pla*nts' green
      highlight.py --word-regexp 'blood' red 'plants' green
    """
    if len(patterns) % 2 != 0:
        print("Error: Each pattern must have a corresponding color", file=sys.stderr)
        sys.exit(1)

    search_patterns = patterns[::2]
    colors = patterns[1::2]

    try:
        highlight(search_patterns, colors, word_regexp)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    argh.dispatch_command(main)
