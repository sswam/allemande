#!/usr/bin/env bash

# <url> <outfile> <start_time> <end_time>
# Clips a video from URL between start and end times

ffclip() {
	eval "$(ally)"

	local url=${1:?URL required}
	local output=${2:?output file required}
	local start=${3:?start time required}
	local end=${4:?end time required}

	# Calculate clip duration
	local len=$(hms "$(calc "$(hms- "$end")" - "$(hms- "$start")")")

	v ffmpeg -y -ss "$start" -i "$url" -t "$len" "$output"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	ffclip "$@"
fi

# version: 0.1.1
