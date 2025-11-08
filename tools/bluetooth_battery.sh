#!/usr/bin/env bash
# [user's name]
# List Bluetooth devices and their battery level as TSV: battery%<TAB>device_id<TAB>name

bluetooth-battery() {
	local paired= p= # if set (1), list only paired devices

	eval "$(ally)" # options, -e -u -o pipefail, and usage

	if ! command -v bluetoothctl >/dev/null 2>&1; then
		die "bluetoothctl not found; install BlueZ tools"
	fi

	local cmd="devices"
	if [ "$paired" = 1 ]; then
		cmd="paired-devices"
	fi

	local devices_output
	# bluetoothctl exits 0 even with no devices; still guard to be safe with -e
	devices_output="$(bluetoothctl "$cmd" 2>/dev/null || true)"

	if [ -z "${devices_output:-}" ]; then
		# No known devices; no output (not an error)
		return 0
	fi

	# Print rows: BATTERY<TAB>ADDR<TAB>NAME
	printf '%s\n' "$devices_output" |
	while IFS= read -r line; do
		# Expect lines like: "Device AA:BB:CC:DD:EE:FF Name With Spaces"
		[ -z "$line" ] && continue
		case "$line" in
		Device\ *)
			;;
		*)
			# Unknown line format; skip but continue processing
			printf >&2 '%s\n' "unexpected line from bluetoothctl $cmd: $line"
			continue
			;;
		esac

		local rest addr name info battery alias
		rest=${line#Device }
		addr=${rest%% *}
		name=${rest#"$addr"}
		# Trim single leading space from name if present
		if [ "${name# }" != "$name" ]; then
			name=${name# }
		fi

		# Query more info (may include battery and alias); do not fail the script if it errors
		info="$(bluetoothctl info "$addr" 2>/dev/null || true)"

		# Prefer Alias from info if present (more human-friendly)
		alias="$(printf '%s\n' "$info" | awk -F': ' '/^Alias: /{print $2; exit}')"
		if [ -n "$alias" ]; then
			name=$alias
		fi

		# Extract first token that looks like NN% from any line mentioning battery/percent
		battery="$(printf '%s\n' "$info" | awk '
			BEGIN{IGNORECASE=1}
			/battery|percent/ {
				for (i=1;i<=NF;i++) {
					if ($i ~ /^[0-9]+%$/) { print $i; exit }
				}
			}
		')"

		# Sanitize fields: replace tabs/newlines to keep strict TSV
		name=$(safe-field "$name")
		battery=$(safe-field "$battery")

		printf -- "%s\t%s\t%s\n" "$battery" "$addr" "$name"
	done
}

safe-field() {
	# Replace tabs and newlines with spaces; leave other characters intact
	# Input may be empty; always print something (possibly empty)
	local s="$*"
	s=${s//$'\t'/ }
	s=${s//$'\n'/ }
	s=${s//$'\r'/ }
	printf -- "%s" "$s"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	bluetooth-battery "$@"
fi

# version: 0.1.0
