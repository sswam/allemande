#!/usr/bin/env bash
# Run Python 3 with the Allemande environment.
set -e -u
if [ -z "${ALLEMANDE_HOME:-}" ]; then
	if [ -d "/opt/allemande" ]; then
		ALLEMANDE_HOME="/opt/allemande"
	elif [ -d "$HOME/allemande" ]; then
		ALLEMANDE_HOME="$HOME/allemande"
	else
		echo >&2 "Error: Could not find ALLEMANDE_HOME"
		exit 120
	fi
fi
if [ -z "${ALLEMANDE_ENV:-}" ]; then
	unset VIRTUAL_ENV
	. "$ALLEMANDE_HOME/env.sh"
fi
exec "$ALLEMANDE_HOME/venv/bin/python3" "$@"
