#!/bin/sh
cmd=${1#^} file=$2
case "$cmd" in
[0-9])
	dir=$cmd
	mkdir -p "$dir"
	mv -n "$file" "$dir"/
	;;
D)
	i3_popup_xterm -g=160x80 lessit image_debug.sh "$file"
	;;
P)
	i3_popup_xterm -g=160x80 lessit image-params "$file"
	;;
O)
	mv "$file" ~/outputs/
	;;
*)
	echo >&2 "Unknown command: $cmd"
	exit 1
	;;
esac
