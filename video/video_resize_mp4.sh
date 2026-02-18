#!/usr/bin/env bash

# <input_video> [output_mp4]
# Convert video to fast start MP4, optionally downscaling to specified height

# shellcheck disable=SC1007,SC2034

video-resize-mp4() {
	local height= h=  # target height in pixels (maintains aspect ratio)

	eval "$(ally)"

	local input_video=$1
	local output_mp4=${2:-}

	if [ -z "$input_video" ]; then
		die "input video file required"
	fi

	if [ ! -f "$input_video" ]; then
		die "input file not found: $input_video"
	fi

	# Set default output filename: input basename without extension, plus .height.mp4
	if [ -z "$output_mp4" ]; then
		local base="${input_video%.*}"
		if [ -n "$height" ]; then
			output_mp4="${base}.${height}.mp4"
		else
			output_mp4="${base}.mp4"
		fi
	fi

	# Build ffmpeg command
	local ffmpeg_args=(
		-i "$input_video"
		-c:v libx264
		-preset medium
		-crf 23
		-c:a aac
		-b:a 128k
	)

	# Add scaling filter if height specified
	if [ -n "$height" ]; then
		ffmpeg_args+=(-vf "scale=-2:$height")
	fi

	ffmpeg_args+=(
		-movflags +faststart
		-y
		"$output_mp4"
	)

	ffmpeg "${ffmpeg_args[@]}"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	video-resize-mp4 "$@"
fi

# version: 0.1.1
