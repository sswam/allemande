#!/bin/bash -eu

# [prog.py] "instructions to improve it" [reference files ...]
# improve a program using AI

m=c	# model
s=0	# refer to hello.<ext> for code style

. opts

prog=$1
prompt=${2-}
shift 2 || true
refs=("$@")

if [ ! -e "$prog" ]; then
	prog2=`wich $prog`
	if [ ! -e "$prog2" ]; then
		echo >&2 "not found: $prog"
		exit 1
	fi
	prog=$prog2
fi

dir=$(dirname "$prog")
base=$(basename "$prog")
ext=.${base##*.}
if [ "$ext" == ".$base" ]; then
	ext=""
fi

# Code style reference and prompt for -s options
if [ "$s" = 1 ]; then
	refs+=("hello$ext")
	prompt="in the style of \`hello$ext\`, $prompt"
fi

prompt="Please improve \`$base\`, $prompt"

input=$(cat_named.py -p -b "$prog" "${refs[@]}")

(
	cd "$dir"
	if [ -e "$base~" ]; then
		move-rubbish "$base~"
	fi
	yes n | cp -i -a "$base" "$base~"   # WTF, there's no proper no-clobber option?!
)

printf "%s\n" "$input" | process -m="$m" "$prompt" | markdown_code.py -c '#' > "$prog~"

(
	cd "$dir"
	swapfiles "$base" "$base~"
	vimdiff "$base" "$base~"
)
