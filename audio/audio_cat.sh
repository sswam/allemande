#!/usr/bin/env bash

# [sam]
# General-purpose audio concat script: output file followed by input files, using ffmpeg

# shellcheck disable=SC1007,SC2034  # Disable certain shellcheck rules that conflict with ally options parser syntax

audio_cat() {
	local output="$1"
	shift
	local inputs=("$@")

	eval "$(ally)"

	if [ ${#inputs[@]} -eq 0 ]; then
		echo >&2 "No input files provided"
		exit 1
	fi

	# Build ffmpeg arguments
	local ffargs=()
	local i=0
	local filter=""
	for input in "${inputs[@]}"; do
		ffargs+=(-i "$input")
		filter+="[${i}:a]"
		i=$((i + 1))
	done
	filter+="concat=n=${#inputs[@]}:v=0:a=1[outa]"

	# Run ffmpeg
	ffmpeg "${ffargs[@]}" -filter_complex "$filter" -map "[outa]" "$output"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	audio_cat "$@"
fi

# version: 0.1.1
