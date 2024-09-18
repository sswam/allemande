#!/bin/bash -eu
# [name]
# Says Hello, world

lang=en	# language [fr|de|jp|cn], defaults to English
shopping=()	# array of items for shopping

. opts

who=${1:-world}

greeting="Hello"

case "$lang" in
fr)	greeting="Bonjour" ;;
de)	greeting="Hallo" ;;
jp)	greeting="こんにちは" ;;
cn)	greeting="你好" ;;
esac

printf "%s, %s\n" "$greeting" "$who"

if [ "${#shopping[@]}" -gt 0 ]; then
	echo
	echo "Shopping list:"
	for item in "${shopping[@]}"; do
		printf -- "- %s\n" "$item"
	done
fi
