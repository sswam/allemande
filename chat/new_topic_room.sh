#!/usr/bin/env bash

# I'll edit `new_topic_room.sh` to add the `--prompt -p` option and fix the shellcheck issues.

# [room names...]
# Create new topic room base files using the AI process command

new-topic-room() {
	local model= m=gf  # LLM model
	local prompt= p=   # extra text to add to the prompt

	eval "$(ally)"

	local room
	for room in "$@"; do
		# if $PWD doesn't start with $ALLEMANDE_ROOMS, cd to it
		local pwd
		pwd="$(realpath "$PWD")/"
		if [ "$pwd" = "${pwd#"$ALLEMANDE_ROOMS"/}" ]; then
			echo >&2 "Changing directory to $ALLEMANDE_ROOMS"
			cd "$ALLEMANDE_ROOMS"
		fi

		local base
		for base in new_SFW.bb.base new_NSFW.bb.base; do
			if [ -e "$base" ]; then
				break
			fi
		done

		if [ ! -e "$base" ]; then
			echo >&2 "No base file found."
			exit 1
		fi

		local type=${base%.bb.base}
		type=${type//_/ }
		prompt="Please write a base template for a $type room: ${room}, based on the example, in the exact same structure and format, only one output, no boilerplate or commentary.
The h1 span class can be fire, fame, or rainbow; different visual effects for the room title. Keep any scripts, or HTML comments to invoke the default agent, if present. Do not change the invoked agent. Only change the title, title style, and intro text.
$prompt"

		printf -- "%s -> %s\n" "$base" "$room"
		(
			< "$base" process -m="$model" "$prompt"
			echo
		) >"$room.bb.base"
		cp -n "$room.bb.base" "$room.bb"
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	new-topic-room "$@"
fi

# version: 0.1.2
