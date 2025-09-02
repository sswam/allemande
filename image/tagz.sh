#!/bin/bash
tr ' ' '\n' |
while read query; do
	echo "## $query"
	(
		techo count tag
		grep "$query" ~/tags | sed 's/_/ /g; s/,/\t/;' | kut 2 1 | head -n 100
	) | tsv2markdown
	echo
done
