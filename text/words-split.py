#!/usr/bin/env python3
# words: Losslessly split and join words.
# words -s: Losslessly split a text file into words and other stuff, for diffing, etc.
# words -j: Join the split text back together again.

import sys
import re
import sys
import argparse

def split_text_stream(input_stream, output_stream, clean=False):
    # Split text into words and non-word characters (including whitespace)
    pattern = r'(\w*\W+)'

    for line in input_stream:
        # the training newline is included in the split
        tokens = re.findall(pattern, line)

        # Write tokens to output stream
        for token in tokens:
            if not clean or re.match(r'\w', token):
                output_stream.write(token + '\n')

def join_text_stream(input_stream, output_stream):
    # Join words and non-word characters back together
    previous_token_newline = False

    for line in input_stream:
        token = line.rstrip('\n')

        if token == '' and not previous_token_newline:
            previous_token_newline = True
            output_stream.write('\n')
        elif token != '':
            output_stream.write(token)
            previous_token_newline = False

def main():
    parser = argparse.ArgumentParser(description='Losslessly split and join words.')
    parser.add_argument('-s', '--split', action='store_true', help='Losslessly split a text file into words.')
    parser.add_argument('-j', '--join', action='store_true', help='Join the split text back together again.')
    parser.add_argument('-c', '--clean', action='store_true', help='Clean up the split text (irreversibly).')
    args = parser.parse_args()

    if args.join:
        join_text_stream(sys.stdin, sys.stdout)
    else:
        split_text_stream(sys.stdin, sys.stdout, args.clean)

if __name__ == '__main__':
    main()
