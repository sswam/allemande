#!/usr/bin/env bash

# image ...
# Creates a montage from input images

image-montage() {
	local output= o=montage.png   # output file name
	local spacing=24              # space between images
	local columns=	              # number of columns

	eval "$(ally)"

	if [ "$#" -eq 0 ]; then
		usage "no input files"
	fi

	# Calculate columns based on square root of number of images
	if [ -z "$columns" ]; then
		columns=$(calc "ceil(sqrt($#))")
	fi

	magick montage "$@" -geometry "+$spacing+$spacing" -tile "${columns}x" "$output"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	image-montage "$@"
fi

# version: 0.1.0
