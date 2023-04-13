#!/bin/bash
ext=mkv
. opts
input=$1
output=${2:-${input}-512.$ext}
time ffmpeg -i "$input" -filter:v "scale=w=512:h=-1:force_original_aspect_ratio=1,pad=512:512:(ow-iw)/2:(oh-ih)/2" -c:a copy "$output"
