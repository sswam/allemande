#!/bin/bash -eu
# searchalot_filter:	Filter searchalot output to show only the most common results

m=0

. opts

min=$m
too_low=$[ $min - 1 ]

cleanup() {
	grep -e '^ *-' -e 'https*:' | sed 's/ *- */- /; s/  */ /g' | sed 's/- The /- /; s/ ([^\t]*//;'
}

minimum_reps() {
	sed -n "/^$too_low\t/q; p"
}

files=( "$@" )

cat "${files[@]}" | cleanup | uniqoc | sort -rn -s | minimum_reps
