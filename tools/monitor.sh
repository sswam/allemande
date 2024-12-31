#!/usr/bin/env bash

# [options]
# Monitors system resources and network connectivity

# The script monitors:
# - Disk space usage
# - System load average
# - Memory usage
# - Basic network connectivity
#
# It outputs warnings on stdout if any of the checks fail.
#
# You can run this script via cron every 5 minutes:
#
# EMAIL="you@example.com"
#
# */5 * * * * /path/to/monitor.sh

monitor() {
	local threshold_storage=  s=95       # storage usage threshold percentage
	local threshold_load=     l=1        # load average threshold
	local threshold_mem=      m=80       # memory usage threshold percentage
	local ping_host=          p=8.8.8.8  # host to ping test

	eval "$(ally)"

	check_disk
	check_load
	check_memory
	check_ping
}

check_disk() {
	df -h | grep -vE '^Filesystem|tmpfs|udev' | awk '{ print $5 " " $6 }' | while read -r percent mountpoint; do
		usage=${percent%%%}
		if [ "$usage" -ge "$threshold_storage" ]; then
			printf "Filesystem mounted at %s is %s%% full!\n" "$mountpoint" "$usage"
		fi
	done
}

check_load() {
	local load_5min
	load_5min=$(uptime | awk -F'load average:' '{ print $2 }' | cut -d, -f2)
	load_5min=${load_5min// /}

	if (($(echo "$load_5min >= $threshold_load" | bc -l))); then
		printf "System load is high: %s (5-minute average)\n" "$load_5min"
	fi
}

check_memory() {
	local memory_usage
	memory_usage=$(free | grep Mem | awk '{print ($2-$7)/$2 * 100.0}')
	memory_usage=${memory_usage%.*}

	if [ "$memory_usage" -ge "$threshold_mem" ]; then
		printf "Memory usage is at %s%%!\n" "$memory_usage"
	fi
}

check_ping() {
	if ! ping -W 1 -c 1 "$ping_host" &>/dev/null; then
		printf "Server cannot ping %s - possible network issues!\n" "$ping_host"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	monitor "$@"
fi

# version: 0.1.0
