#!/bin/bash -eu
# ffmpeg-sub:	extract subtitles from a video file
c=	# clean
. opts

input=$1 sub_index=$2
clean=$c

extract() {
	ffmpeg -v error -i "$input" -map 0:s:$sub_index -c:s copy -f srt -
}

cleanup() {
	grep -vE '^[0-9]+$|^[0-9]{2}:[0-9]{2}:[0-9]{2}'
}

if [ "$clean" = 1 ]; then
	extract | cleanup
else
	extract
fi
