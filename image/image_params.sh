#!/bin/bash
s=0
. opts

for I; do
	info=`ii "$I"`
	echo "$info" | grep '^Steps:' |
	perl -pe 's{(TI hashes: ")(.*?)(")}{$1 . join(", ", keys %{{ map {$_ => 1} split(/, /, $2) }}) . $3}e'

	echo

	echo "$info" | grep '^ *parameters:' |
	sed 's/^ *parameters: */Parameters:\n\n/;' |
	if [ "$s" = 1 ]; then
		cat
	else
		split-prompt
#		sed 's/, */,\n/g' | grep -v '^,$'
	fi

	echo

	echo "Negative prompt:"
	echo
	echo "$info" | grep '^Negative prompt:' |
	sed 's/^Negative prompt: //;' |
	if [ "$s" = 1 ]; then
		cat
	else
		split-prompt
#		sed 's/, */,\n/g' | grep -v '^,$'
	fi

	echo
	echo
done |
highlight.py '<[^>]*>' red || true
