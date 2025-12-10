#!/usr/bin/env bash

# [file ...]
# move to rubbish
# suggested: alias rm=move-rubbish
# moves each file to ~/rubbish/${basename}_${timestamp}
# undo with unrubbish

# shellcheck disable=SC1007,SC2034,SC2086  # Disable certain shellcheck rules that conflict with ally options parser syntax

quiet= q=  # move quietly
xargs= x=  # read filenames from stdin instead of argv

eval "$(ally)"

verbose=""
if ((!quiet)); then
	verbose="-v"
fi

timestamp() {
	date +%Y%m%d_%H%M%S%N%z_%a
}

if [ -z "${RUBBISH:-}" ]; then
	M=$(mount-point "${1:-}")
	if [ "$M" = "$(mount-point "$HOME")" ] || [ "$M" = / ]; then
		RUBBISH="$HOME/.rubbish"
	else
		RUBBISH="$M/.rubbish"
	fi
fi
(umask 0700; mkdir -p "$RUBBISH"; chmod 0700 "$RUBBISH")

move_to_rubbish() {
	local A="$1"
	local N=$(basename -- "$A")
	local B=$(mktemp "$RUBBISH/${N}_XXXXXX")
	if mv $verbose -- "$A" "$B"; then
		if [ -n "${mr_echo:-}" ]; then printf '%s\n' "$B"; fi
	else
		status=1
	fi
}

status=0
if [ "${xargs:-0}" = 1 ]; then
	while IFS= read -r A; do
		move_to_rubbish "$A"
	done
else
	for A; do
		move_to_rubbish "$A"
	done
fi
exit $status
