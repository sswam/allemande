#!/bin/sh
# XXX this is likely SLOW!
# see also canonpath
for A; do
	if [ -e "$A" ]; then
		readlink -f -- "$A"
	else
		echo $(p "`dirname -- "$A"`")/"`basename -- "$A"`"
	fi
done
