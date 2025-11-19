#!/usr/bin/env bash

# [usb_find search_string]
# Find USB device by search string, output device code or full record

# shellcheck disable=SC1007,SC2034  # Disable certain shellcheck rules that conflict with ally options parser syntax

usb-find() {
	local all= a=  # output whole record

	eval "$(ally)"

	local search="$1"
	if [ -z "$search" ]; then
		usage
		return 1
	fi

	local block=""
	while IFS= read -r line; do
		if [[ $line =~ ^T: ]]; then
			if [ -n "$block" ]; then
				if match "$block" "$search"; then
					output "$block" "$all"
				fi
			fi
			block="$line"$'\n'
		else
			block+="$line"$'\n'
		fi
	done < <(usb-devices)

	# Process last block
	if [ -n "$block" ] && match "$block" "$search"; then
		output "$block" "$all"
	fi
}

match() {
	local block="$1" search="$2"
	# Check if search string is in P: or S: lines (case insensitive)
	if printf '%s\n' "$block" | awk -F':' '/^P:/ || /^S:/ { for(i=2; i<=NF; i++) if (tolower($i) ~ tolower("'"$search"'")) { found=1; exit } } END { exit !found }'; then
		return 0
	else
		return 1
	fi
}

output() {
	local block="$1" all="$2"
	if [ "$all" = 1 ]; then
		printf '%s\n' "$block"
	else
		local bus dev
		bus=$(printf '%s\n' "$block" | awk '/^T:/ { match($0, /Bus=([^ ]+)/, a); bus=a[1]; sub(/^0+/, "", bus); if (bus == "") bus="0"; print bus }')
		dev=$(printf '%s\n' "$block" | awk '/^T:/ { match($0, /Dev#=[ ]*([0-9]+)/, a); print a[1] }')

		# Find the actual device path by searching /sys/bus/usb/devices/
		local devpath
		devpath=$(find /sys/bus/usb/devices/ -maxdepth 1 -name "${bus}-*" -type l | while IFS= read -r path; do
			if [ -f "$path/devnum" ] && [ "$(cat "$path/devnum")" = "$dev" ]; then
				basename "$path"
				break
			fi
		done)

		printf '%s\n' "$devpath"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	usb-find "$@"
fi

# version: 0.1.3

# Issues:

# 1. match() function: The awk command incorrectly includes quotes around
# the search string in the regex, preventing matches; it should use -v
# search="$search" to pass the variable properly.
