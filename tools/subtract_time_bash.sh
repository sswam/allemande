#!/bin/bash -eu

end_time=$1
start_time=$2

start_seconds=$(date -d "$start_time" +%s)
end_seconds=$(date -d "$end_time" +%s)

diff_seconds=$((end_seconds - start_seconds))

if [ $diff_seconds -lt 0 ]; then
	echo "Time difference is negative" >&2
	exit 1
fi

printf "%02d:%02d\n" $(($diff_seconds/3600)) $(($diff_seconds%3600/60))
