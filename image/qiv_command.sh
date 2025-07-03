#!/usr/bin/env bash
# key file
# qiv command script

eval "$(ally)"

cmd=${1#^} file=$2
case "$cmd" in
[0-9])
	dir=$cmd
	mkdir -p "$dir"
	if [ "${SYMLINK:-0}" != "0" ]; then
		lnrel "$file" "$dir"/
	else
		mv -n "$file" "$dir"/
	fi
	;;
D)
	i3-xterm-floating -g=160x80 lessit image-debug "$file"
	;;
P)
	i3-xterm-floating -g=160x80 lessit image-params "$file"
	;;
O)
	mv "$file" ~/outputs/
	;;
*)
	echo >&2 "Unknown command: $cmd"
	exit 1
	;;
esac
