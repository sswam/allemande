#!/bin/bash

# [room...]
# Opens chat and sends notification when matching messages appear

open-chat-on-message() {
	local system= s=1      # match system messages only
	local include=() i=()  # array of users to match
	local exclude=() x=()  # array of users to exclude
	local timeout= t=60    # notify-send timeout in seconds

	eval "$(ally)"

	local paths=()

	for room; do
		paths+=("$ALLEMANDE_ROOMS_SERVER/$room.bb")
	done

	# awatch -r -x bb -p "${paths[@]}" -f meta,text |
	# while IFS=$'\t' read -r room type oldsize newsize text

	(
		. reaper
		for room; do
			path="$ALLEMANDE_ROOMS_SERVER/$room.bb"
			v atail -p 1 -n 0 -f -w --restart "$path" |
			while read line; do
				printf "$room\t%s\n" "$line"
			done &
		done
		wait
	) |
	while IFS=$'\t' read -r room text
	do
		user=${text%%:*}
		if [ "$user" = "$text" ]; then
			continue
		fi

		if [ "${#exclude[@]}" -gt 0 ]; then
			# Skip if user is in exclude list
			for excluded in "${exclude[@]}"; do
				if [ "$user" = "$excluded" ]; then
					continue 2
				fi
			done
		elif [ "${#include[@]}" -gt 0 ]; then
			# Skip if user not in include list
			matched=0
			for included in "${include[@]}"; do
				if [ "$user" = "$included" ]; then
					matched=1
					break
				fi
			done
			if [ "$matched" = 0 ]; then
				continue
			fi
		elif [ "$system" = 1 ] && [ "$user" != "System" ]; then
			continue
		fi

		# chrome --new-window "https://chat.allemande.ai/#$room"
		notify-send -t "$timeout" -u critical "Ally Chat" "New message from $user in $room."
		now=$(date +%F\ %a\ %T)
		printf "%s\t%s\t%s\t%s\n" "$now" "$room" "$user" "$text"
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	open-chat-on-message "$@"
fi

# TODO redo in Python
# version: 0.1.6
