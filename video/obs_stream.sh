#!/usr/bin/env bash
# Fix OBS camera by resetting USB device

obs-stream() {
	local start_streaming= s=1  # start OBS streaming automatically
	local reset_camera= r=1     # reset camera/s before streaming
	local wait_time= w=1        # seconds to wait after USB reset
	local exit= x=              # stop obs

	eval "$(ally)"

	local obs_running
	check_obs_running

	if [ "$exit" = 1 ] && [ "$obs_running" = 0 ]; then
		warn "OBS is not running; cannot exit."
		return 0
	fi
	if [ "$exit" = 1 ]; then
		info "Exiting OBS..."
		pkill -x obs
		return 0
	fi

	if [ "$reset_camera" = 1 ]; then
		reset_camera
	fi

	check_obs_running

	start_obs
}

reset_camera() {
	info "Resetting camera USB device(s)..."
	# Find camera/webcam USB devices
	local usb_info
	usb_info=$(lsusb | grep -i -e camera -e webcam)
	while IFS= read -r line; do
		# Extract bus and device numbers (e.g., "Bus 007 Device 002")
		if ! [[ $line =~ Bus\ ([0-9]+)\ Device\ ([0-9]+) ]]; then
			continue
		fi
		local bus="${BASH_REMATCH[1]}"
		local device="${BASH_REMATCH[2]}"
		local usb_path="${bus}/${device}"
		info "Resetting USB device: $usb_path"
		sudo usbreset "$usb_path"
	done <<< "$usb_info"

	# Wait for device/s to reset
	sleep "$wait_time"
}

start_obs() {
	if [ "$obs_running" = 1 ]; then
		warn "OBS is already running; cannot start streaming."
		return 0
	fi
	if [ "$start_streaming" = 1 ]; then
		info "Starting OBS with streaming..."
		q obs --startstreaming &
	else
		info "Starting OBS..."
		q obs &
	fi
}

check_obs_running() {
	obs_running=0
	if q pgrep -x obs; then
		obs_running=1
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	obs-stream "$@"
fi

# version: 0.1.0
