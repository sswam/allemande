#!/usr/bin/env python3-allemande

import spacy
import sys
import re
import argparse

def segment_text_into_sentences(text, nlp):
	""" Split a text into sentences using spaCy's sentence segmentation. """
	doc = nlp(text)
	for sent in doc.sents:
		yield sent.text

dot_point_re = re.compile(r'^[-*\u2022\u25E6\u2023]\s')

def group_lines_into_paragraphs(stream):
	""" Collects lines into paragraphs. """
	paragraph = []
	for line in stream:
		line = line.rstrip()
		if dot_point_re.match(line):
			paragraph.append(line+"\n")
		elif line:
			paragraph.append(line+" ")
		else:
			yield "".join(paragraph)
			paragraph = []
	if paragraph:
		yield "".join(paragraph)

def format_sentences_as_lines(inp, nlp):
	if isinstance(inp, str):
		inp = StringIO(inp)
	pgs = list(group_lines_into_paragraphs(inp))
	first = True
	for pg in pgs:
		if not first:
			yield ""
		pg = pg.rstrip()
		if dot_point_re.match(pg):
			yield pg
		else:
			sentences = list(segment_text_into_sentences(pg, nlp))
			if sentences:
				yield "\n".join(sentences)
		first = False

def split_sentences_test(text, nlp):
	return "\n".join(format_sentences_as_lines(text, nlp))

def main():
	parser = argparse.ArgumentParser(description='Split sentences')
	parser.add_argument('-m', '--model', default='en_core_web_sm', help='Model to use')
	args = parser.parse_args()

	nlp = spacy.load(args.model)

	for line in format_sentences_as_lines(sys.stdin, nlp):
		print(line)

import pytest
from io import StringIO

@pytest.fixture
def nlp():
	return spacy.load("en_core_web_sm")

def test_edge_cases(nlp):
	# simulate an input stream from text...
	assert split_sentences_test("Hello\nworld.", nlp) == "Hello world."
	assert split_sentences_test("", nlp) == ""
	assert split_sentences_test("Two. Sentences.", nlp) == "Two.\nSentences."
	assert split_sentences_test("- foo\n- bar", nlp) == "- foo\n- bar"

if __name__ == "__main__":
	main()
