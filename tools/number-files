#!/bin/bash -eu

b="%02d. "	# format string for beginning
m="%s"	# format string for original filename
e=	# format string for end
i=1	# start index
s=1	# step
o="mv -iv --"	# operation

. opts

while read file; do
	new="`printf "$b" "$i"``printf "$m" "$file"``printf "$e" "$i"`"
	$o "$file" "$new"
	i=$((i+s))
done
