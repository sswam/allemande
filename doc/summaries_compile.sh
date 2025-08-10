#!/usr/bin/env bash
cat "$ALLEMANDE_AGENTS/dirs.txt" |
while read dir; do
	echo "### $dir" | title
	echo
	(
		cd "$ALLEMANDE_AGENTS/$dir"
		find . -name '*.yml' | sort | while read -r file; do
			A=$(basename "$file" .yml)
			echo -n "- $A - "
			cat "$ALLEMANDE_HOME/doc/summary/$A.txt" || echo
		done
	)
	echo
done
