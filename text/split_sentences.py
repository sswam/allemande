#!/usr/bin/env python3-allemande

import sys
import regex
import argparse
from io import StringIO
import subprocess

__version__ = '0.1.5'


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


# Build pattern: match exceptions, sentence ends, or any character
# Sort exceptions by length (longest first) to match greedily
SORTED_EXCEPTIONS = sorted(EXCEPTIONS, key=len, reverse=True)
EXCEPTION_PATTERN = '|'.join(regex.escape(exc) for exc in SORTED_EXCEPTIONS)

# Terminal punctuation that requires whitespace (Western, Indic, Arabic)
STOP_WESTERN = r"[.!?।؟፤།]"

# Terminal punctuation that does NOT require whitespace (CJK / Asian)
STOP_CJK = r"[。！？」』]"

# Closing brackets, quotes, and punctuation that might clip
# onto the end of a sentence (e.g., the quote in: He said, "No!")
CLOSING_MODIFIERS = r"[\"'\)\]}»›”’]"

# Global opening brackets, quotes, dashes, or inverted markers that
# might introduce a new sentence (e.g., ¿ or ¡ in Spanish)
OPENING_MODIFIERS = r"[\"'({{[‚„«‹“‘「『¿¡—–]"

# In Western languages, a sentence starts with an upper-case character.
UPPERCASE = r"[\p{Lu}\p{Lo}]"

# Pattern matches:
# 1. Exceptions - don't split
# 2. Sentence endings (punctuation + optional spaces before uppercase/quote/punct)
# Allow quotes, parens, or whitespace before the capital letter for proper sentence detection

SENTENCE_PATTERN = rf"""
    (  # 1. exceptions
        {EXCEPTION_PATTERN}
    )
|
    (  # 2. stop mid text
        {STOP_WESTERN}+
        {CLOSING_MODIFIERS}*
        \s+  # require spacing
        |
        {STOP_CJK}+
        \s*
    )
    (?=  # lookahead to start of next sentence
        {OPENING_MODIFIERS}*
        \s*
        {UPPERCASE}
    )
"""

def split_sentences(text):
	"""
	Split text into sentences using regex substitution.
	Handles common abbreviations, titles, and other exceptions that contain periods
	but don't mark sentence boundaries.

	Uses a two-token approach: exceptions (leave as-is), sentence endings (add newline).
	"""
	if not text or not text.strip():
		return []

	def replace_func(match):
		# Exception - leave as is
		if match.group(1):
			return match.group(1)
		# Sentence end before capital letter (with possible quotes/punctuation) - add newline
		if match.group(2):
			return match.group(2) + '\n'
		raise AssertionError("logic error in split_sentences.replace_func")

	result = regex.sub(SENTENCE_PATTERN, replace_func, text, flags=regex.VERBOSE)

	# Split on newlines and clean up
	sentences = [s.strip() for s in result.split('\n')]
	return [s for s in sentences if s]


def split_sentences_spacy(text, nlp):
	""" Split a text into sentences using spaCy's sentence segmentation. """
	doc = nlp(text)
	for sent in doc.sents:
		yield sent.text

dot_point_re = regex.compile(r'^[-*\u2022\u25E6\u2023]\s')

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

def format_sentences_as_lines(inp, splitter):
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
			sentences = list(splitter(pg))
			for sentence in sentences:
				yield sentence
		first = False

def split_sentences_test(text, splitter):
	return "\n".join(format_sentences_as_lines(text, splitter))


def main():
	parser = argparse.ArgumentParser(description='Split sentences')
	parser.add_argument('-m', '--model', default='en_core_web_sm', help='Spacy model to use')
	parser.add_argument('-s', '--spacy', action='store_true', help='Use slower spacy splitting')
	args = parser.parse_args()

	if args.spacy:
		import spacy
		try:
			nlp = spacy.load(args.model)
		except OSError:
			print(f"Downloading spacy model '{args.model}'...", file=sys.stderr)
			subprocess.check_call([sys.executable, "-m", "spacy", "download", args.model])
			nlp = spacy.load(args.model)

		def spacy_splitter(text):
			return split_sentences_spacy(text, nlp)

		splitter = spacy_splitter
	else:
		splitter = split_sentences

	for line in format_sentences_as_lines(sys.stdin, splitter):
		print(line)

if __name__ == "__main__":
	main()
