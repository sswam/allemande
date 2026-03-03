#!/usr/bin/env bash

# <input_video> [output_mp4]
# Convert video to fast start MP4, optionally downscaling to specified height

# shellcheck disable=SC1007,SC2034

video-resize-mp4() {
	local height= h=  # target height in pixels (maintains aspect ratio)
	local language= l=  # audio language to keep when multiple tracks exist, e.g. eng

	eval "$(ally)"

	local input_video=$1
	local output_mp4=${2:-}

	if [ -z "$input_video" ]; then
		die "input video file required"
	fi

	if [ ! -f "$input_video" ]; then
		die "input file not found: $input_video"
	fi

	# Default language
	if [ -z "$language" ]; then
		language=eng
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

	# Select audio track by language if multiple audio streams exist
	local audio_count
	audio_count=$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$input_video" 2>/dev/null | wc -l)
	if [ "$audio_count" -gt 1 ]; then
		ffmpeg_args+=(-map 0:v:0 -map "0:a:m:language:$language")
	fi

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

# version: 0.1.2
