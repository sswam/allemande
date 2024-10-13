#!/bin/bash -eu
# [file ...]
# AI praise

m=	# model
p=	# prompt

. opts

prompt=$p

praise() {
	prompt="Please provide some friendly and supportive praise and encouragement regarding this.
The author needs some help with some self-esttem\!
e.g. if it seems like a cool program that does something useful or novel...
$prompt"
	main_file="${1:--}"
	shift || true
	cat-named -b -p "$main_file" "$@" |
	(process -m="$m" "$prompt"; echo) |
	tee -a -- "$main_file.praise"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	praise "$@"
fi
