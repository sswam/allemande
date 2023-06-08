#!/bin/bash -eu
# silence-remover:	use ffmpeg to remove silence from an audio file

i=${1:--}	# input file
o=${2:--}	# output file
p=-1	# what's this?
d=1	# seconds
t=-30	# dB

. opts

in=$i
out=$o
stop_periods=$p
stop_duration=$s
stop_threshold=$d

ffmpeg -i "$in" -af "silenceremove=stop_periods=$stop_periods:stop_duration=$stop_duration:stop_threshold=${stop_threshold}dB" "$out"
