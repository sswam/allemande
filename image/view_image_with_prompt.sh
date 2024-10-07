#!/bin/bash

x=0
s=0

. opts

set -e -u -o pipefail

x_screen=$x
small=$s

if [ -d "${1:-}" ]; then
	find "$@" -mindepth 1 -maxdepth 1 -name '*.png' | sort | "$0" "${OPTS[@]}"
	exit $?
fi

if [[ "${1:-}" == *.* ]]; then
	lecho "$@" | "$0" "${OPTS[@]}"
	exit $?
fi

if [ "$small" = 1 ]; then
	small=100
fi

start=${1:-}

if [ -n "$start" ]; then
	v sed -n "/$start/,\$p"
else
	cat
fi | (
trap 'exit 1' INT
while read I; do
	if [[ "$I" != *.png ]]; then
		echo "$I"
		continue
	fi
	clear
	echo "$I"
	echo
	image-params "$I"

	if [ "$small" = 0 ]; then
		qiv --fullscreen --scale_down --xineramascreen ${x_screen:-0} "$I"
	else
		qiv -w "$small" --xineramascreen ${x_screen:-1} "$I"
	fi
done
)
