#!/bin/bash
# runs "lock" to dissuade the user from working at night

conf_file=~/.hopeofsleepatnightrc

sleep_time=2300
wake_time=0500
poll_interval_night=1s
poll_interval_day=5m
override_duration=10m
override_file=~/.emergency_override
lock_process=i3lock
lock_command=lock

if [ -f "$conf_file" ]; then
	. "$conf_file"
fi

trap '' SIGINT SIGTERM  # can only kill with kill -9

is_day() {
	time=$(date +%H%M)
	if [ $wake_time -lt $sleep_time ] && [ $time -ge $wake_time -a $time -lt $sleep_time ]; then
		return 0
	elif [ $wake_time -ge $sleep_time ] && [ $time -ge $wake_time -o $time -lt $sleep_time ]; then
		return 0
	else
		return 1
	fi
}

lock_at_night() {
	if is_day; then
		sleep $poll_interval_day
	elif [ -e "$override_file" ]; then
		override_val=$(cat "$override_file")
		rm -f "$override_file"
		sleep "${override_val:-$override_duration}"
	elif pidof "$lock_process" >/dev/null; then
		sleep $poll_interval_night
	else
		$lock_command
		sleep $poll_interval_night
	fi
}

hopeofsleeptonight() {
	if [ "$1" == "--abandon-all" ]; then
		echo "$2" > "$override_file"
		echo "Override set for ${2:-${override_duration}}."
		exit 0
	fi

	while true; do
		lock_at_night
	done
}

hopeofsleeptonight "$@"
