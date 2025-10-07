#!/bin/bash
set -e -u -o pipefail
while true; do
	pid=$(pgrep -f 'python3 .* ally_chat.py' || true)
	if [ -z "$pid" ]; then
		sleep 1
		continue
	fi
	py-spy top -p "$pid" || true
done
