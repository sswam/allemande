#!/bin/bash -eu
# input_video output_video
# Convert an mp4 video to fast start mp4, with the MOOV atom at the start of the file, without reencoding.
eval "$(ally)"
input_video=$1
output_video=${2:-}
replace_input_video=0
if [ -z "$output_video" ]; then
	output_video=$(mktemp "${input_video%.*}.XXXXXXXX.mp4")
	replace_input_video=1
fi
ffmpeg -y -v warning -i "$input_video" -movflags +faststart -codec copy "$output_video"
touch -r "$input_video" "$output_video"
chmod --reference="$input_video" "$output_video"
if [ $replace_input_video -eq 1 ]; then
	mv "$output_video" "$input_video"
fi
