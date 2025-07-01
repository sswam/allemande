#!/usr/bin/env bash
#
# Uses AI to find good regexps to split a text into chunks, based on an initial portion.

head -c 30000 | process -m=s 'Please identify good places to split this text into chunks for processing by an LLM, such as chapter boundaries, or failing that perhaps section or paragraph boundaries, and write regexps that would identify such boundary points. Include a regexp for each type of boundary point starting with the highest level one, and moving down to finish with the lowest-level one larger than a single line, e.g. a paragraph. Do include low-level boundaries like paragraphs, as a "chapter" might be too large to process in one go. Combine those at the same level into a single regexp if possible (e.g. chapter headings and appendix headings). None of the regexps should match false-positives.

An example ouput might be:

level_1: ^\s*(CHAPTER|APPENDIX)\s*\d*\s*$
level_2: ^\s*$

Please output a few lines with keys (level_1 etc) and regexps only.
' | process "These regexps are intended to match high and lower level section boundaries in a text file. Please combine any that should be at the same semantic level, remove any that would likely match false-positives, and generally sanity-check them. Output the regexps in a similar format. The purpose is to split the text into chunks small enough to be processed by an LLM. We would split using the highest level regexp, then split any chunks that are too large using the next lower-level regexp and so on. The regexps should ideally be fairly generic but not match false positives. If we need to split into small chunks we will combine chunks at the same level to be processed together, subject to context-window limits. E.g. we might appeand 3 chapters together, or we might append 50 paragraphs together, for processing. With this in mind, please improve the list of regexps as needed." | grep '^level_[0-9][0-9]*: ' | sed 's/^level_[0-9]*: //'
