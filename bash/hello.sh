#!/bin/bash -eu
# Hello, world

# usage:
#	$0 [-lang=<cc>] <name>
# example:
#	$0 -lang=fr Sam
#	$0 -lang=de -shopping,cake,milk,'jelly\ beans' $USER

lang=en
shopping=()

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
