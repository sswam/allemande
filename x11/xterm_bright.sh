#!/bin/bash -eu
# [arg ...]

percent="$1"
shift

resources="$HOME/conf/Xresources"

if [ ! -L "$resources" ]; then
	echo >&2 "Not a symlink: $resources"
	exit 1
fi

old="$(readlink "$resources")"

tmp="$resources.$$.tmp"

< "$resources.100" hex-adjust "$percent" > "$tmp"

ln -sf "$tmp" "$resources"
xrdb -merge "$resources"

xterm "$@" &

sleep 0.1

ln -sf "$old" "$resources"
xrdb -merge "$resources"
