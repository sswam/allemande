#!/usr/bin/env bash
# <mission_file> <visual_file> <script>
# Updates last line of mission and visual files based on script execution

scene-time() {
	eval "$(ally)"

	local mission_file=$1
	local visual_file=$2
	local dates_file=${3:-}
	local times_file=${4:-}

	time=$(date +%H%M%S)
	date=$(date +%m%d)

	local date_prompts="\t" time_prompts="\t"
	if [ -e "$dates_file" ]; then
		date_prompts=$(peep -b "$date" "$dates_file" | kut 2 3)
	fi
	if [ -e "$times_file" ]; then
		time_prompts=$(peep -b "$time" "$times_file" | kut 2 3)
	fi
	IFS=$'\t' read -r mission1 visual1 <<< "$date_prompts"
	IFS=$'\t' read -r mission2 visual2 <<< "$time_prompts"

	# Replace last two lines in each file
	(head -n -2 "$mission_file" ; echo "$mission1" ; echo "$mission2") > "$mission_file".tmp.$$
	(head -n -2 "$visual_file" ; echo "$visual1" ; echo "$visual2") > "$visual_file".tmp.$$
	mv "$mission_file".tmp.$$ "$mission_file"
	mv "$visual_file".tmp.$$ "$visual_file"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	scene-time "$@"
fi
