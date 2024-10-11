#!/usr/bin/env bash
# key file
# qiv command script

eval "$(ally)"

cmd=${1#^} file=$2
case "$cmd" in
[0-9])
	dir=$cmd
	mkdir -p "$dir"
	mv -n "$file" "$dir"/
	;;
D)
	i3-popup-xterm -g=160x80 lessit image-debug "$file"
	;;
P)
	i3-popup-xterm -g=160x80 lessit image-params "$file"
	;;
O)
	mv "$file" ~/outputs/
	;;
*)
	echo >&2 "Unknown command: $cmd"
	exit 1
	;;
esac
