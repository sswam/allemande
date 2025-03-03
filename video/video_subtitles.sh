#!/usr/bin/env bash

# <input file> <subtitle index>
# Extract subtitles from a video file

video-subtitles() {
	local clean= c=      # remove timestamps and numbers

	eval "$(ally)"

	local input=$1
	local sub_index=$2

	if [ "$clean" = 1 ]; then
		extract | cleanup
	else
		extract
	fi
}

extract() {
	ffmpeg -v error -i "$input" -map "0:s:$sub_index" -c:s copy -f srt -
}

cleanup() {
	grep -vE '^[0-9]+$|^[0-9]{2}:[0-9]{2}:[0-9]{2}'
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	video-subtitles "$@"
fi

# version: 0.1.1
