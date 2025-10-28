#!/usr/bin/env bash
# <path>
# Returns an available filename by appending numbers if needed

get-available-name() {
	local file= f=       # create a file, avoids race conditions
	local directory= d=  # create a directory, avoids race conditions

	eval "$(ally)"

	local extension=
	local base="$1"

	if [ -z "$base" ]; then
		die "Path argument required"
	fi

	local dirname=$(dirname -- "$base")
	local filename=$(basename -- "$base")

	# Extract extension if present
	if [[ $filename = ?*.* ]]; then
		extension=".${filename##*.}"
		filename="${filename%.*}"
		base="$dirname/$filename"
	fi

	local target="$base$extension"
	local counter=0

	if [ -n "$file" ] && [ -n "$directory" ]; then
		die "Cannot specify both --file and --directory"
	fi

	while true; do
		if [ -n "$file" ]; then
			if (set -o noclobber; : > "$target") 2>/dev/null; then
				break
			fi
		elif [ -n "$directory" ]; then
			if mkdir "$target" 2>/dev/null; then
				break
			fi
		elif [ ! -e "$target" ]; then
			break
		fi

		target="${base}-${counter}${extension}"
		((++counter))
	done

	printf "%s\n" "$target"
}

if [ "${BASH_SOURCE[0]}" == "$0" ]; then
	get-available-name "$@"
fi

# version: 0.1.2
