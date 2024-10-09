#!/bin/bash -eu
# file1 file2

copy= c=	# copy to preserve hard links

eval "$(ally)"

if [ "$copy" = 1 ]; then
	cp -i "$1" "$1.tmp.$$"
	cp "$2" "$1"
	cp "$1.tmp.$$" "$2"
	rm "$1.tmp.$$"
else
	mv -i "$1" "$1.tmp.$$"
	mv -i "$2" "$1"
	mv -i "$1.tmp.$$" "$2"
fi
