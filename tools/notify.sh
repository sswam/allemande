#!/bin/bash -eu
message="$*"
echo >&2 "$message"
if command -v notify-send 2>/dev/null; then
	notify-send "$message"
else
	mail -s "$HOSTNAME: notify: $message" "$USER" <<-END
	$message
	END
fi
