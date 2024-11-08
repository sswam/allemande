#!/bin/bash -eu
# Run Python 3 with the Allemande environment.
if [ -z "${ALLEMANDE_ENV:-}" ]; then
	unset VIRTUAL_ENV
	. "$ALLEMANDE_HOME/env.sh"
fi
exec "$ALLEMANDE_HOME/venv/bin/python3" "$@"
