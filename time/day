#!/bin/bash -eu
# show date in a nice format, and optional time
t=	# show time
s=" "	# separator
d="now"	# date
W=	# no weekday

. opts

time=$t
sep=$s
when=$d

# the format
fmt="%Y-%m-%d"
if ! [ "$W" ]; then
	fmt="$fmt$sep%a"
fi
if [ "$time" ]; then
	fmt="$fmt$sep%H:%M:%S"
fi

date +"$fmt" -d "$when"
