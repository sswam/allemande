#!/bin/bash -eu
# fc:	add flashcards

f="$HOME/my/flashcards.txt"
b="v q arcs"
l=

. opts

file=$f
backup=$b
list=$l

if [ "$list" = 1 ]; then
	less "$file"
	exit
else
	echo >> "$file"
	vim + "$file"
fi
if [ -n "$backup" ]; then
	$b "$file"
fi
