#!/bin/bash -eu
# [name]
# Says Hello, world

l=en	# language [fr|de|jp|cn], defaults to English
s=()	# array of items for shopping

. opts

who=${1:-world}

greeting="Hello"

case "$l" in
fr)	greeting="Bonjour" ;;
de)	greeting="Hallo" ;;
jp)	greeting="こんにちは" ;;
cn)	greeting="你好" ;;
esac

printf "%s, %s\n" "$greeting" "$who"

if [ "${#s[@]}" -gt 0 ]; then
	echo
	echo "Shopping list:"
	for item in "${s[@]}"; do
		printf -- "- %s\n" "$item"
	done
fi
