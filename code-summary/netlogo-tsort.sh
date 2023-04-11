#!/bin/bash -eu

# netlogo-tsort.sh: Sort NetLogo files by dependency

# TODO: This is a hack.  It should be rewritten in Python.

for module in `lsd`; do
	(
		cd "$module"
		for A in *.nls; do
			# skip files matching unknown-*
			if [[ "$A" =~ unknown-.* ]]; then
				continue
			fi
			echo "$A	$A"
			func_name="${A%.*}"
			for B in *.nls; do
				if [ "$A" = "$B" ]; then continue; fi
				if < "$B" sed 's/;.*//' | q fgrep "$func_name"; then
					echo "$A	$B"
				fi
			done
		done |
		tee deps1.txt |
		tsort > bottom-up.txt
		< deps1.txt kut 2 1 | tsort > top-down.txt
	)
done
