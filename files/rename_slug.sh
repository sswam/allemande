#!/bin/bash
# source
# rename a file using a slugified file stem

eval "$(ally)"

source="$1"

filename=$(basename "$source")
dirname=$(dirname "$source")

# Handle dotfiles: strip leading dot before slugging, add it back after
dotprefix=""
if [[ "$filename" == .* ]]; then
	dotprefix="."
	filename="${filename#.}"
fi

# Extract extension if present
if [[ "$filename" == *.* ]]; then
	extension="${filename##*.}"
	name="${filename%.*}"
	slugified="$dotprefix$(slug "$name").$extension"
else
	slugified="$dotprefix$(slug "$filename")"
fi

target="$dirname/$slugified"

[ "$target" = "$source" ] || mv "$source" "$dirname/$slugified"

# version 0.0.4
