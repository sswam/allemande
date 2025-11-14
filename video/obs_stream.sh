#!/usr/bin/env bash
# Fix OBS camera by resetting USB device

obs-camera-fix() {
	local start_streaming= s=1  # start OBS streaming automatically
	local reset_camera= r=1     # reset camera/s before streaming
	local wait_time= w=1        # seconds to wait after USB reset
	local quit= q=              # stop obs
	local toggle= t=            # start or stop obs

	eval "$(ally)"

	if [ "$quit" = 1 ]; then
		echo >&2 "Quitting OBS..."
		pkill -x obs
		return 0
	fi

	if [ "$reset_camera" != 1 ]; then
		echo >&2 "Skipping camera reset as per user request."
	else
		echo >&2 "Resetting camera USB device(s)..."
	fi
	# Find camera/webcam USB devices
	local usb_info
	usb_info=$(lsusb | grep -i -e camera -e webcam)

	# Process each camera found
	while IFS= read -r line; do
		# Extract bus and device numbers (e.g., "Bus 007 Device 002")
		if [[ $line =~ Bus\ ([0-9]+)\ Device\ ([0-9]+) ]]; then
			local bus="${BASH_REMATCH[1]}"
			local device="${BASH_REMATCH[2]}"
			local usb_path="${bus}/${device}"

			echo >&2 "Resetting USB device: $usb_path"

			sudo usbreset "$usb_path"
		fi
	done <<< "$usb_info"

	# Wait for device to reset
	sleep "$wait_time"

	# Check if OBS is running
	if ! pgrep -x obs >/dev/null 2>&1; then
		echo >&2 "Starting OBS..."

		# Start OBS, optionally with streaming
		if [ "$start_streaming" = 1 ]; then
			q obs --startstreaming &
		else
			q obs &
		fi
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	obs-camera-fix "$@"
fi

# version: 0.1.0

# WIP - NOT FINISHED!

# Crit:
# 1. The reset_camera flag check only prints a message; USB reset always runs
# regardless. The reset block should be conditional when skipping is requested.
# 2. usbreset is invoked with "bus/device" (e.g., "007/002"); most usbreset
# tools expect a device path like "/dev/bus/usb/007/002". Current argument
# may fail.
# 3. Bash function name uses a hyphen (obs-camera-fix); hyphens are not valid
# in bash function names. Consider obs_camera_fix.
# 4. toggle (t) option is declared but unused; either implement its behavior or
# drop the option to avoid confusion.
# 5. Suggestion: initialize defaults on the long option vars too (e.g.,
# start_streaming=1, reset_camera=1, wait_time=1) to avoid relying on ally
# mirroring short -> long for defaults.
