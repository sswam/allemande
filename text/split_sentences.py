#!/usr/bin/env python3-allemande

import sys
import re
import argparse
from io import StringIO
import subprocess

__version__ = '0.1.4'


# Common abbreviations and titles that shouldn't trigger sentence breaks
EXCEPTIONS = [
	# Titles
	'Mr.', 'Mrs.', 'Ms.', 'Miss.', 'Dr.', 'Prof.', 'Sr.', 'Jr.',
	'Rev.', 'Fr.', 'Msgr.', 'Gen.', 'Col.', 'Maj.', 'Capt.', 'Lt.',
	'Sgt.', 'Cpl.', 'Sen.', 'Rep.', 'Gov.', 'Pres.', 'Hon.',

	# Academic degrees
	'Ph.D.', 'M.D.', 'B.A.', 'M.A.', 'B.S.', 'M.S.', 'J.D.', 'LL.B.',
	'D.D.S.', 'Pharm.D.', 'M.B.A.', 'Ed.D.', 'Esq.',

	# Common abbreviations
	'etc.', 'vs.', 'viz.', 'Inc.', 'Ltd.', 'Corp.', 'Co.', 'LLC.',
	'Dept.', 'Univ.', 'Assn.', 'Bros.', 'Ph.', 'EST.', 'PST.', 'MST.', 'CST.',

	# Time and measurements
	'Jan.', 'Feb.', 'Mar.', 'Apr.', 'Jun.', 'Jul.', 'Aug.', 'Sep.', 'Sept.',
	'Oct.', 'Nov.', 'Dec.', 'Mon.', 'Tue.', 'Tues.', 'Wed.', 'Thu.', 'Thur.',
	'Thurs.', 'Fri.', 'Sat.', 'Sun.', 'a.m.', 'p.m.', 'A.M.', 'P.M.',
	'approx.', 'min.', 'max.', 'no.', 'No.', 'vol.', 'Vol.', 'pp.', 'cf.',

	# Latin abbreviations
	'i.e.', 'e.g.', 'et al.', 'ibid.', 'loc. cit.', 'op. cit.',

	# Locations
	'St.', 'Ave.', 'Blvd.', 'Rd.', 'Dr.', 'Ln.', 'Ct.', 'Sq.', 'Apt.',
	'U.S.', 'U.K.', 'U.S.A.', 'E.U.', 'U.N.',

	# Misc
	'fig.', 'Fig.', 'al.', 'seq.', 'tel.', 'ext.', 'misc.',
	'p.', 'P.', 'Mt.', 'Ft.', 'v.', 'V.'
]


def segment_text_into_sentences_simple(text):
	"""
	Split text into sentences using regex substitution.
	Handles common abbreviations, titles, and other exceptions that contain periods
	but don't mark sentence boundaries.

	Uses a three-token approach: exceptions (leave as-is), sentence endings (add newline),
	and other characters (leave as-is).
	"""
	if not text or not text.strip():
		return []

	# Build pattern: match exceptions, sentence ends, or any character
	# Sort exceptions by length (longest first) to match greedily
	sorted_exceptions = sorted(EXCEPTIONS, key=len, reverse=True)
	exception_pattern = '|'.join(re.escape(exc) for exc in sorted_exceptions)

	# Pattern matches:
	# 1. Exceptions - don't split
	# 2. Sentence endings (punctuation + optional spaces before uppercase/quote/punct)
	# 3. Sentence endings at end of string
	# Allow quotes, parens, or whitespace before the capital letter for proper sentence detection
	pattern = rf"""({exception_pattern})|([.!?]+(?:\.\.\.)?)\s+(?=["\'(\[{{‚„'"]?\s*[A-Z\u00C0-\u00DC])|([.!?]+)$"""

	def replace_func(match):
		# Exception - leave as is
		if match.group(1):
			return match.group(1)
		# Sentence end before capital letter (with possible quotes/punctuation)
		if match.group(2):
			# Sentence end before capital letter
			return match.group(2) + '\n'
		# Sentence end at end of string
		if match.group(3):
			return match.group(3)
		return match.group(0)

	result = re.sub(pattern, replace_func, text)

	# Split on newlines and clean up
	sentences = [s.strip() for s in result.split('\n')]
	return [s for s in sentences if s]


def segment_text_into_sentences_spacy(text, nlp):
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

def format_sentences_as_lines(inp, segmenter):
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
			sentences = list(segmenter(pg))
			for sentence in sentences:
				yield sentence
		first = False

def split_sentences_test(text, segmenter):
	return "\n".join(format_sentences_as_lines(text, segmenter))


def main():
	parser = argparse.ArgumentParser(description='Split sentences')
	parser.add_argument('-m', '--model', default='en_core_web_sm', help='Spacy model to use')
	parser.add_argument('-s', '--simple', action='store_true', help='Use simple regex-based splitting (fast, no dependencies)')
	args = parser.parse_args()

	if args.simple:
		segmenter = segment_text_into_sentences_simple
	else:
		import spacy
		try:
			nlp = spacy.load(args.model)
		except OSError:
			print(f"Downloading spacy model '{args.model}'...", file=sys.stderr)
			subprocess.check_call([sys.executable, "-m", "spacy", "download", args.model])
			nlp = spacy.load(args.model)

		def spacy_segmenter(text):
			return segment_text_into_sentences_spacy(text, nlp)

		segmenter = spacy_segmenter

	for line in format_sentences_as_lines(sys.stdin, segmenter):
		print(line)

if __name__ == "__main__":
	main()
