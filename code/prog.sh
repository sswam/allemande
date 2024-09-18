#!/bin/bash -eu
# [prog.py] "instructions to create it" [reference files ...]
# write a program using AI

m=c	# model
s=1	# refer to hello.<ext> for code style

. opts

prog=$1
prompt=${2-}
shift 2 || true
refs=("$@")

if [ -e "$prog" ]; then
	echo >&2 "already exists: $prog"
	exit 1
fi

ext=.${prog##*.}
if [ "$ext" == ".$base" ]; then
	ext=""
fi

if [ "$s" = 1 ]; then
	refs+=("hello$ext")
	prompt="in the style of \`hello$ext\`, $prompt"
fi

dir=`dirname "$prog"`
base=`basename "$prog"`

mkdir -p "$dir"

prompt="Please \`write\` $base, $prompt"

input=$(v cat_named.py -p -b "${refs[@]}")

printf "%s\n" "$input" | v process -m="$m" "$prompt" | markdown_code.py -c '#' > "$prog"

chmod +x "$prog"
vi "$prog"
