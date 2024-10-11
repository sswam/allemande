#!/usr/bin/env bash
# [file ...]
# Look up the Debian package that provides each file.

eval "$(ally)"

for file; do
	basename=${file##*/}
	dlocate $(which-file "$basename") | grep "/$basename\$" | sed 's/: /\t/'
done
