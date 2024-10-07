#!/bin/bash
# select-types:	Selects all the types of files in the results directory
while read type; do
#	Y=`sl_gify "$X"`
	type_esc=$(echo "$type" | sed 's/[^a-zA-Z0-9]/_/g; s/__*/_/g; s/^_//; s/_$//')
	ls results | grep -i "\.${type_esc}_in_[A-Z]"
done
