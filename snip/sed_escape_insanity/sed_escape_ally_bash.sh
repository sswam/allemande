#!/usr/bin/env bash
# [arg ...]
# Escape special characters in the given text for use in a sed regular expression.
# Also escapes any characters passed in "$2" (optional), which had better not include / or ].

E= extended=0	# escape for sed ERE regular expressions.

eval "$(ally)"	# magically sets -eu, handles options -E == --extended, and provides usage(), etc.

text="$1" || usage "Missing text argument."
extras="${2:-}"
[ "$#" -le 2 ] || usage "Too many arguments."

metachars='][.*^$/\&'
extended="+?|(){}"

if ((extended)); then
	metachars="$metachars$extended"
fi

sed "s/[$metachars$extras]/"'\\&/g' <<< "$text"
