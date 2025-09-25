#!/bin/bash -eu
# Create new topic room base files using the AI process command

for room; do
	# if $PWD doesn't start with $ALLEMANDE_ROOMS, cd to it
	pwd="$(realpath "$PWD")/"
	if [ "$pwd" = "${pwd#"$ALLEMANDE_ROOMS"/}" ]; then
		echo >&2 "Changing directory to $ALLEMANDE_ROOMS"
		cd "$ALLEMANDE_ROOMS"
	fi

	for base in new_SFW.bb.base new_NSFW.bb.base; do
		if [ -e "$base" ]; then
			break
		fi
	done

	if [ ! -e "$base" ]; then
		echo "No base file found." >&2
		exit 1
	fi

	type=${base%.bb.base}
	type=${type//_/ }
	prompt="Please write a base template for a $type room: ${room}, based on the example, in the exact same structure and format, only one output, no boilerplate or commentary.
The h1 span class can be fire, fame, or rainbow; different visual effects for the room title. Keep any scripts, or HTML comments to invoke a default agent, if present. Only change the title, title style, and intro text."

	echo "$base -> $room"
	(
		< "$base" process -m=gf "$prompt"
		echo
	) >"$room.bb.base"
	cp -n "$room.bb.base" "$room.bb"
done
