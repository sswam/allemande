#!/bin/bash -eu
output_image=$1 width=$2 height=$3
convert -size "${width}x${height}" xc: +noise Random "$output_image"
