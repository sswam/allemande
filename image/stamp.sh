#!/bin/bash

# Manipulate image comment metadata, such as image generation parameters
# Usage: image_comment action [options] input [output]
# Actions: extract, insert, erase, copy, convert

# Examples:
#   image_comment extract input.png
#   image_comment insert -i metadata.txt input.png
#   image_comment erase input.jpg
#   image_comment copy input.png output.jpg
#   image_comment convert -f jpg -q 90 input.png output.jpg

image_comment() {
	# Options:
	local o=    # output file
	local i=    # metadata input file (for insert)
	local m=    # modify in place
	local q=95  # JPEG quality for conversion
	local f=    # output format (for convert)

	# Source the opts file for option parsing
	. opts

	# Enable strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	# Get the action and shift arguments
	local action="${1:-}"
	shift || true

	# Check if action is provided
	if [ -z "$action" ]; then
		echo "Error: No action specified."
		return 1
	fi

	# Check for required commands
	if ! command -v magick &>/dev/null; then
		echo "Error: magick command not found."
		return 1
	fi
	if ! command -v exiftool &>/dev/null; then
		echo "Error: exiftool command not found."
		return 1
	fi

	# Handle different actions using a case statement
	case "$action" in
		extract)
			# Extract metadata from input image
			local input="${1:-}"
			local output="${o:-${2:-}}"

			if [ -z "$input" ]; then
				echo "Error: No input image specified."
				return 1
			fi

			extract_metadata "$input" "$output"
			;;

		insert)
			# Insert metadata into input image
			local input="${1:-}"
			local metadata_file="${i:-${2:-}}"

			if [ -z "$input" ] || [ -z "$metadata_file" ]; then
				echo "Error: Input image and metadata file are required."
				return 1
			fi

			insert_metadata "$input" "$metadata_file" "$m"
			;;

		erase)
			# Erase metadata from input image
			local input="${1:-}"
			local output="${o:-${2:-}}"

			if [ -z "$input" ]; then
				echo "Error: No input image specified."
				return 1
			fi

			erase_metadata "$input" "$output" "$m"
			;;

		copy)
			# Copy metadata from input to output image
			local input="${1:-}"
			local output="${o:-${2:-}}"

			if [ -z "$input" ] || [ -z "$output" ]; then
				echo "Error: Input and output images are required."
				return 1
			fi

			copy_metadata "$input" "$output"
			;;

		convert)
			# Convert image format and copy metadata
			local input="${1:-}"
			local output="${o:-${2:-}}"

			if [ -z "$input" ]; then
				echo "Error: No input image specified."
				return 1
			fi

			convert_image "$input" "$output" "$f" "$q"
			;;

		*)
			echo "Error: Unknown action '$action'."
			return 1
			;;
	esac

	# Restore original options
	eval "$old_opts"
}

# Function to extract metadata from an image
extract_metadata() {
	local input="$1"
	local output="$2"

	# Extract Comment metadata using ImageMagick
	local sd_metadata
	sd_metadata=$(magick identify -format '%[parameters]' "$input") || true

	# Output metadata to file or stdout
	if [ -n "$sd_metadata" ]; then
		if [ -n "$output" ]; then
			printf "%s\n" "$sd_metadata" > "$output"
			echo "Metadata extracted to $output."
		else
			printf "%s\n" "$sd_metadata"
		fi
	else
		echo "No Comment metadata found in $input."
	fi
}

# Function to insert metadata into an image
insert_metadata() {
	local input="$1"
	local metadata_file="$2"
	local modify_in_place="${3:-}"

	# Check if metadata file exists and is not empty
	if [ ! -f "$metadata_file" ]; then
		echo "Error: Metadata file '$metadata_file' not found."
		return 1
	fi

	# Read metadata from file
	local sd_metadata
	sd_metadata=$(<"$metadata_file")

	# Check if metadata is not empty
	if [ -z "$sd_metadata" ]; then
		echo "Error: Metadata file '$metadata_file' is empty."
		return 1
	fi

	# Determine output file
	local output="$input"
	if [ -z "$modify_in_place" ]; then
		output="${input%.*}_with_metadata.${input##*.}"
		cp "$input" "$output"
	fi

	# Insert metadata using exiftool
	exiftool -overwrite_original -preserve "-UserComment=$sd_metadata" "$output" &>/dev/null

	echo "Metadata inserted into $output."
}

# Function to erase metadata from an image
erase_metadata() {
	local input="$1"
	local output="${2:-}"
	local modify_in_place="${3:-}"

	# Determine output file
	if [ -z "$modify_in_place" ]; then
		if [ -z "$output" ]; then
			output="${input%.*}_no_metadata.${input##*.}"
		fi
		cp "$input" "$output"
	else
		output="$input"
	fi

	# Erase all metadata using exiftool
	exiftool -overwrite_original -all= "$output" &>/dev/null

	echo "Metadata erased from $output."
}

# Function to copy metadata from one image to another
copy_metadata() {
	local input="$1"
	local output="$2"

	# Extract Comment metadata
	local sd_metadata
	local ext="${input##*.}"
	case "$ext" in
	png)
		sd_metadata=$(magick identify -format '%[parameters]' "$input") || true
		;;
	jpg|jpeg|tif|tiff|webp)
		sd_metadata=$(exiftool -b -UserComment "$input") || true
		;;
	*)
		echo "Unsupported file format"
		exit 1
		;;
	esac

	# Check if metadata exists
	if [ -z "$sd_metadata" ]; then
		echo "No Comment metadata found in $input."
		return 1
	fi

	# Copy metadata to output image using exiftool
	exiftool -overwrite_original -preserve "-UserComment=$sd_metadata" "$output" &>/dev/null

	echo "Metadata copied from $input to $output."
}

# Function to convert image format and copy metadata
convert_image() {
	local input="$1"
	local output="$2"
	local format="${3:-jpg}"
	local quality="${4:-95}"

	# Determine format from output file extension if not provided
	if [ -z "$format" -a -n "$output" ]; then
		format="${output##*.}"
	fi

	# Determine output file name if not provided
	if [ -z "$output" ]; then
		output="${input%.*}.$format"
	fi

	# Convert image using ImageMagick
	magick convert "$input" -quality "$quality" "$output"

	# Copy metadata to converted image
	copy_metadata "$input" "$output"
}

# Run the main function if the script is executed directly
if [ "$BASH_SOURCE" = "$0" ]; then
	image_comment "$@"
fi
