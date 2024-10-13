#!/bin/bash

# [source image]
# Generates favicons from a source image

favicon() {
	local source= s=	# source image
	local sizes=() S=(16 32 48 64 128 144 180 192 256)	# sizes

	eval "$(ally)"

	# Check for required commands
	check_command convert || return 1
	check_command identify || return 1

	# Display script version
	echo "Favicon Generator v1.0.3"

	# Ensure we're in the correct directory
	echo "You need to run this from a directory containing only the PNG icons and no other files."
	echo "It will overwrite any existing PNG files."
	confirm "Are you in the icons directory?" || return 1

	# Validate source file
	if [ -z "$source" ]; then
		echo >&2 "Error: Please provide the source image file."
		return 1
	fi
	source=$(readlink -f "$source")
	if [ ! -f "$source" ]; then
		echo >&2 "Error: Source file '$source' does not exist."
		return 1
	fi
	chmod -w "$source"

	# Create temporary directory
	local temp_dir=$(mktemp -d)
	trap 'rm -rf "$temp_dir"' RETURN

	# Create temporary images
	v convert "$source" -resize 512x512 -background white -gravity center -extent 512x512 "$temp_dir/tmp-512-white.png"
	v convert "$source" -resize 512x512 "$temp_dir/tmp-512.png"

	# Generate favicons
	generate_favicons

	# Process other PNG files
	process_png_files

	echo "Favicon generation complete."

	# restore caller options
	eval "$old_opts"
}

check_command() {
	if ! command -v "$1" &> /dev/null; then
		echo >&2 "Error: $1 is not installed. Please install it and try again."
		return 1
	fi
}

generate_favicons() {
	local favicons=()
	for size in "${sizes[@]}"; do
		local filename="favicon-${size}x${size}.png"
		v convert "$temp_dir/tmp-512.png" -resize ${size}x${size} "$filename"
		favicons+=("$filename")
	done

	# Create favicon.ico
	v convert "${favicons[@]}" -colors 256 favicon.ico
}

process_png_files() {
	for file in *.png; do
		case "$file" in
			favicon-*)
				continue
				;;
			apple-touch-icon*)
				v convert "$temp_dir/tmp-512-white.png" -resize $(identify -format "%wx%h" "$file") "$file"
				;;
			*)
				v convert "$temp_dir/tmp-512.png" -resize $(identify -format "%wx%h" "$file") "$file"
				;;
		esac
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	favicon "$@"
fi
