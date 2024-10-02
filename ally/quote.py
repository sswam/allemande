"""
Quoting utilities, useful for tests especially.
"""

import textwrap

__version__ = "0.1.0"

def quote(multiline_string):
    """Remove any common leading whitespace from every line in the input string."""
    s = textwrap.dedent(multiline_string)
    if s.startswith("\n"):
        return s[1:]
    return s

def quote_lines(multiline_string):
    """Convert a multiline string into a list of lines with common leading whitespace removed and no trailing newlines."""
    output = quote(multiline_string).split("\n")
    if output and output[-1] == "":
        output.pop()
    return output

def quote_lunks(multiline_string):
    """Convert a multiline string into a list of lines with common leading whitespace removed, including trailing newlines."""
    output = quote_lines(multiline_string)
    return [x+"\n" for x in output]

def quote_words(string):
    """Convert a string into a list of words with common leading whitespace removed."""
    return string.split()

def quote_paragraphs(multiline_string):
    """Convert a multiline string into a list of paragraphs with common leading whitespace removed."""
    return quote(multiline_string).split("\n\n")

def quote_blocks(multiline_string):
    """Convert a multiline string into a list of blocks with common leading whitespace removed."""
    return quote(multiline_string).split("\n\n\n")

# At this points the developer lost his presence of mind ...

def quote_sentences(string):
    """Convert a string into a list of sentences with common leading whitespace removed."""
    import nltk
    nltk.download('punkt')
    from nltk.tokenize import sent_tokenize
    return sent_tokenize(string)

def quote_words_extreme_edition(string):
    """Convert a string into a list of words with common leading whitespace removed, properly exlude punctuation."""
    import nltk
    nltk.download('punkt')
    from nltk.tokenize import word_tokenize
    return word_tokenize(string)

# We don't want to be quoting things with great long function names, so ...

qi = quote
ql = quote_lines
qL = quote_lunks
qw = quote_words
qp = quote_paragraphs
qb = quote_blocks
qs = quote_sentences
qW = quote_words_extreme_edition
