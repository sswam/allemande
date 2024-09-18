#!/bin/bash -eu
# [prog.py] "instructions to create it" [reference files ...]
# write a program using AI

m=c	# model
h=1	# refer to hello.ext if no other references provided

. opts

prog=$1
prompt=${2-}
shift 2

ext=${prog##*.}

if [ "$h" = 1 ] && [ $# = 0 ]; then
	refs=("hello.$ext")
		prompt="in the style of hello.$ext, $prompt"
else
	refs=("$@")
fi

dir=`dirname "$prog"`
base=`basename "$prog"`

mkdir -p "$dir"

prompt="Please write $base, $prompt"

v cat_named.py -p -b "${refs[@]}" | v process -m="$m" "$prompt" | markdown_code.py -c '#' > "$prog"

chmod +x "$prog"
vi "$prog"
