#!/usr/bin/env bash
cat "$ALLEMANDE_AGENTS/dirs.txt" |
while read dir; do
	echo "### $dir" | title
	echo
	(
		cd "$ALLEMANDE_AGENTS/$dir"
		for A in *.yml; do
			A=${A%.yml}
			echo -n "- $A - "
			cat "$ALLEMANDE_HOME/doc/summary/$A.txt"
		done
	)
	echo
done
