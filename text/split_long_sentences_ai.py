#!/usr/bin/env python3-allemande
""" ai_split_long_sentences.py: split long sentences into shorter ones using an LLM """

from sys import stdin, stdout
from io import StringIO

from argh import dispatch_command

import gpt


def splitter(line):
	""" Split a line into sentences using an LLM """
	prompt = "If the following seems too long, please split it into smaller sentences by editing punctuation only. Don't add or remove any words. Only reply with the edited text or the the original text, no commentary or questions."

	# TODO automatically handle strings vs streams

	inp = StringIO(line)
	out = StringIO()

	gpt.process(inp, out=out, prompt=prompt)

	return out.getvalue()


def split_long_sentences_ai(inp=stdin, out=stdout, long=80):
	"""Split long sentences into shorter ones using an LLM"""
	for line in inp:
		if len(line) - 1 > long:
			line = splitter(line).rstrip()
		print(line, file=out, flush=True)


if __name__ == '__main__':
	dispatch_command(split_long_sentences_ai)
