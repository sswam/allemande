#!/bin/bash
# catpg: concatenate files, with paragraph breaks
break=
. opts
for A; do
	cat "$A"
	printf "%s\n" "$break"
done
