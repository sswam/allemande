#!/bin/bash
# catpg: concatenate files, with paragraph breaks

break= b=	# break text
last= l=	# append break at end

eval "$(ally)"

count=0
total=$#
for file; do
	((++count))
	cat "$file"
	if ((last)) || [ $count -lt $total ]; then
		printf "%s\n" "$break"
	fi
done
