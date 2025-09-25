#!/usr/bin/env bash

# [file] [count]
# Updates extra characters in chat room file

update-extra-characters() {
	eval "$(ally)"

	local file=${1:-"Ally Chat.m"}
	local count=${2:-50}

	cd "$ALLEMANDE_ROOMS"

	if [ ! -f "$file" ]; then
		die "file not found: $file"
	fi

	local nsfw=0
	local categories="$categories_sfw"
	local exclude="nsfw"
	# if starts with nsfw/
	if [[ "$file" = "nsfw/"* ]]; then
		nsfw=1
		categories="$categories $categories_nsfw"
		exclude="sfw"
	fi

	# Remove last line from file
	modify head -n -1 : "$file"

	# Generate character list
	(
		cd "$ALLEMANDE_AGENTS"
		find $categories -name '.*' -o -name "$exclude" -prune -o -type f -name '*.yml' -printf "%f\n"
	) | sed 's/\.yml//' |
		shuf |
		head -n "$count" |
		sed 's/$/, /' |
		tr -d '\n' |
		sed 's/, $/\n/' >> "$file" || true
}

categories_sfw="cartoon character disney fiction game"
categories_nsfw="nsfw"
categories_other="art base model celeb comedy extra human muppet over poet personal religion search short special tool toon visual wip"

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	update-extra-characters "$@"
fi

# version: 0.1.1
