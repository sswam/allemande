#!/bin/bash
LC_ALL=C comm -2 -3 <(ls summary/ | sed 's/\.txt$//' | LC_ALL=C sort) <(< agent_colours.tsv kut 1 | LC_ALL=C sort) |
while read A; do
	echo -n "- $A - "
	cat summary/"$A.txt"
done | tee /dev/stderr |
process -m=lite "Please output tab-separated TSV with three columns: name,color1,color2.
- name is the first part from an agent / character line, e.g. Mr Biddle.
- color1 is a CSS HSL color to show that character's name in the chat,
  on a white background, preferably fairly dark, and reflecting the character in some way.
- color2 is the same color but with lightness inverted for dark mode on a black background." |
grep -v -e '```' -e '^name	' | grep '	.*	.*)' |
tee -a agent_colours.tsv
