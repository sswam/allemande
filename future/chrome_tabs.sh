#!/bin/bash

#
# Retrieves open tab URLs from Chrome

chrome_tabs() {
	local p=	# Chrome profile name
	local d=	# Custom Chrome data directory
	local f=text	# Output format [text|json]

	. opts

	# Strict mode
	local old_opts=$(set +o)
	set -euo pipefail

	# Determine operating system
	local OS="$(uname)"
	local urls=()

	case "${OS}" in
		"Darwin")
			# macOS: Use AppleScript to get Chrome tabs
			local apple_script='
			tell application "Google Chrome"
				set window_list to every window
				set all_tabs to {}
				repeat with the_window in window_list
					set tab_list to every tab in the_window
					repeat with the_tab in tab_list
						set end of all_tabs to URL of the_tab
					end repeat
				end repeat
				return all_tabs
			end tell
			'
			urls=($(osascript -e "$apple_script"))
			;;
		"Linux")
			# Linux: Use Chrome's Remote Debugging Protocol
			# Ensure Chrome is started with --remote-debugging-port=9222
			# Example: google-chrome --remote-debugging-port=9222 &
			if ! pgrep -x "chrome" > /dev/null; then
				echo >&2 "Error: Chrome is not running with --remote-debugging-port=9222"
				return 1
			fi

			# Get open tabs via curl
			local tabs_json=$(curl -s http://localhost:9222/json)
			urls=($(echo "$tabs_json" | jq -r '.[].url'))
			;;
		*)
			echo >&2 "Error: Unsupported operating system: ${OS}"
			return 1
			;;
	esac

	# Output results
	if [ "$f" = "json" ]; then
		printf '{\n  "urls": [\n'
		for url in "${urls[@]}"; do
			printf '	"%s",\n' "$url"
		done | sed '$ s/,$//'
		printf '  ]\n}\n'
	else
		for url in "${urls[@]}"; do
			printf '%s\n' "$url"
		done
	fi

	# Restore caller options
	eval "$old_opts"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	chrome_tabs "$@"
fi

# version 0.1.2
