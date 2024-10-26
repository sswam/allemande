#!/bin/bash -eu
# input_video output_video
# Convert an mp4 video to fast start mp4, with the MOOV atom at the start of the file, without reencoding.
eval "$(ally)"
input_video=$1
output_video=$2
ffmpeg -i "$input_video" -movflags +faststart -c copy "$output_video"
