#!/bin/bash
# file1 file2
# Swap the names of two files

copy= c=	# copy to preserve hard links

eval "$(ally)"

if [ "$#" -ne 2 ]; then
	echo "swapfiles: wrong number of arguments" >&2
	exit 1
fi

from="$1"
to="$2"

if [ ! -e "$from" ] || [ ! -e "$to" ]; then
	echo "swapfiles: files do not both exist" >&2
	exit 1
fi

if [ "$copy" = 1 ]; then
	cp -i "$from" "$from.tmp.$$"
	cp "$to" "$from"
	cp "$from.tmp.$$" "$to"
	rm "$from.tmp.$$"
else
	mv -i "$from" "$from.tmp.$$"
	mv -i "$to" "$from"
	mv -i "$from.tmp.$$" "$to"
fi
