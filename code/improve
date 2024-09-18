#!/bin/bash -eu
# [prog.py] "instructions to improve it" [reference files ...]
# improve a program using AI

m=c	# model

. opts

prog=$1
prompt=${2-}
shift 2
refs=("$@")

if [ ! -e "$prog" ]; then
	prog2=`wich $prog`
	if [ ! -e "$prog2" ]; then
		echo >&2 "not found: $prog"
		exit 1
	fi
	prog=$prog2
fi

dir=`dirname "$prog"`
base=`basename "$prog"`

(
	cd "$dir"
	git add "$base"
	cp -a "$base" "$base~"
)

prompt="Please improve $base, $prompt"

cat_named.py -p -b "$prog" "${refs[@]}" | process -m="$m" "$prompt" | markdown_code.py -c '#' > "$prog~"

(
	cd "$dir"
	swapfiles "$base" "$base~"
	vimdiff "$base" "$base~"
	mr "$base~"
)
