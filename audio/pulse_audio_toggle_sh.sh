#!/usr/bin/env bash

# PulseAudio Toggle - Switch between audio outputs

pulse_audio_toggle() {
	local list= l=  # list available sinks
	local info= i=  # show current sink
	local quiet= q= # suppress output

	eval "$(ally)"

	local state_file=~/.local/state/pulse_audio_toggle.sh
	local sink_num="${1:-}"
	mkdir -p "$(dirname "$state_file")"

	# Get current and previous sinks from state file
	local curr_sink= prev_sink=
	if [ -f "$state_file" ]; then
		# shellcheck source=/dev/null
		. "$state_file"
	fi

	# Get current system sink
	sys_sink=$(pactl get-default-sink)
	sys_sink=$(pactl list sinks | grep -B2 "Name: $sys_sink" | grep 'Sink #' | sed 's/Sink #//')

	if [ "$info" = 1 ]; then
		pactl list sinks | grep -A3 "^Sink #$sys_sink\$" |
			sed -n 's/.*Description: \(.*\)/'"$sys_sink"'\t\1/p'
		return
	fi

	if [ "$list" = 1 ]; then
		pactl list sinks | grep -e '^Sink' -e 'Description:' |
			sed -n 'N;s/Sink #\([0-9]*\)[^D]*Description: \(.*\)/\1\t\2/p' |
			while IFS=$'\t' read -r num desc; do
				if [ "$num" = "$curr_sink" ]; then
					printf "*"
				else
					printf " "
				fi
				printf " %s\t%s\n" "$num" "$desc"
			done
		return
	fi

	if [ -n "$sink_num" ]; then
		# Set specific sink
		if ! pactl list sinks | grep -q "^Sink #$sink_num\$"; then
			die "invalid sink number: $sink_num"
		fi
		prev_sink=$curr_sink
		curr_sink=$sink_num
	else
		# Toggle between sinks
		if [ -n "$prev_sink" ] && [ "$prev_sink" != "$curr_sink" ]; then
			local temp=$curr_sink
			curr_sink=$prev_sink
			prev_sink=$temp
		fi
	fi

	pactl set-default-sink "$curr_sink"
	printf "curr_sink=%s\nprev_sink=%s\n" "$curr_sink" "$prev_sink" >"$state_file"

	if [ "$quiet" != 1 ]; then
		pactl list sinks | grep -A3 "^Sink #$curr_sink\$" |
			sed -n 's/.*Description: \(.*\)/'"$curr_sink"'\t\1/p'
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	pulse_audio_toggle "$@"
fi
