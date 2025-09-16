#!/bin/bash
# runs "lock" to dissuade the user from working at night

sleep_time=2300
wake_time=0500
poll_interval_night=5  # check every 5 seconds during night
poll_interval_day=300  # check every 5 minutes during day
override_file=$HOME/.emergency_override  # touch this file to skip locking once
override_duration=600  # override lasts for 10 minutes
lock_process=i3lock
lock_command=lock

. ~/.hopeofsleepatnightrc

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
		rm -f "$override_file"
		sleep $override_duration
	elif pidof "$lock_process" >/dev/null; then
		sleep $poll_interval_night
	else
		$lock_command
		sleep $poll_interval_night
	fi
}

hopeofsleeptonight() {
	while true; do
		lock_at_night
	done
}

hopeofsleeptonight
