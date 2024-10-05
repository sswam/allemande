#!/usr/bin/env bash

# [input_file]
# Create images for a document using AI image generator

illustrate() {
	local input_file=${1:-}	# Input file name
	local output_dir= o=.	# Output directory for images
	local model= m=sdxl	# AI model to use
	local width= w=1024	# Image width
	local height= h=1024	# Image height

	eval "$(ally)"

	[ -n "$input_file" ] || usage "Input file is required"
	[ -f "$input_file" ] || die "Input file '$input_file' does not exist"

	mkdir -p "$output_dir"

	process_file "$input_file"
}

process_file() {
	local file=$1
	local line
	local alt_text
	local filename

	while IFS= read -r line; do
		if [[ $line =~ \!\[([^\]]+)\]\(([^\)]+)\) ]]; then
			# Markdown image
			alt_text="${BASH_REMATCH[1]}"
			filename="${BASH_REMATCH[2]}"
			generate_image "$alt_text" "$filename"
		elif [[ $line =~ \<img[^>]+alt="([^"]+)"[^>]+src="([^"]+)" ]]; then
			# HTML image
			alt_text="${BASH_REMATCH[1]}"
			filename="${BASH_REMATCH[2]}"
			generate_image "$alt_text" "$filename"
		elif [[ $line =~ \[image:\ ([^\]]+)\] ]]; then
			# Text format image
			alt_text="${BASH_REMATCH[1]}"
			filename=$(echo "$alt_text" | tr ' ' '_' | tr -dc '[:alnum:]_-').png
			generate_image "$alt_text" "$filename"
		fi
	done < "$file"
}

generate_image() {
	local alt_text=$1
	local filename=$2
	local output_path="$output_dir/$filename"

	echo "Generating image for: $alt_text" >&2
	imagen -o "$output_path" \
		-p "$alt_text" \
		--width "$width" \
		--height "$height" \
		--sampler-name "DPM++ 2M" \
		--scheduler "Karras" \
		--steps 30 \
		--cfg-scale 7 \
		--count 1 \
		--model "$model"

	if [ $? -eq 0 ]; then
		echo "Image saved as: $output_path" >&2
	else
		echo "Failed to generate image for: $alt_text" >&2
		return 1
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	illustrate "$@"
fi
