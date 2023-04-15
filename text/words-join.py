#!/usr/bin/env python3
# words-join: Join words and non-word characters back together from a split text file
import sys

def join_text_stream(input_stream, output_stream):
	previous_token_newline = False

	for line in input_stream:
		token = line.rstrip('\n')

		if token == '' and not previous_token_newline:
			previous_token_newline = True
			output_stream.write('\n')
		elif token != '':
			output_stream.write(token)
			previous_token_newline = False

if __name__ == '__main__':
	join_text_stream(sys.stdin, sys.stdout)
