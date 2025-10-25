#!/usr/bin/env bash
# <dirname> <youtube-url>
# Downloads online video and creates transcription

yt-stt() {
	eval "$(ally)"

	local name=${1:-}
	local url=${2:-}

	if [ -z "$name" ] || [ -z "$url" ]; then
		die "usage: $(basename "$0") <dirname> <youtube-url>"
	fi

	mkdir -p "$name"
	(
		cd "$name"
		yt-dlp "$url"
		video=$(ls) || die "no video file found"
		audio="audio.mp3"
		text="text.txt"
		ffmpeg -i "$video" "$audio"
		whisper-cpp "$audio"
		mv "${audio%.*}.txt" "$text"
	)
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	yt-stt "$@"
fi

# version: 0.1.1
