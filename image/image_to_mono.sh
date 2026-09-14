#!/bin/bash -eu

# [options]
# Convert an image to greyscale and crop grey range for white background, black forground (text)

low= l=30   # max percentage for black
high= h=70  # min percentage for white

eval "$(ally)"

for img; do
	magick "$img" -colorspace gray -level "$low%,$high%" "mono_$img"
done
