#!/usr/bin/env bash
# < requirements.txt
# Tries to install each package in requirements.txt one by one
# and logs the ones that fail to broken_packages.$$.txt

eval "$(ally)"

while read pkg; do
	if [ -z "$pkg" ] || [[ "$pkg" == \#* ]]; then
		continue
 	fi
	echo "$pkg"
done |
while read pkg; do
	v pip install "$pkg" || echo "$pkg" >> broken_packages.$$.txt
done
