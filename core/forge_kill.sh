#!/usr/bin/env bash
# Kill the automatic1111 stable diffusion webui process,
# if case of failure, so it will restart and hopefully work!
# Depends on our use of /opt/venvs/python3.10-automatic1111
forge-kill() {
	local signal= s=TERM       # signal code to use [TERM|STOP|CONT], defaults to TERM

	eval "$(ally)"

	PID=$(psgrep forge/venv | awk '{print $2}')
	if [ -n "$PID" ]; then
		set -x
		kill -$signal $PID || true  # shellcheck disable=SC2086
		set +x
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	forge-kill "$@"
fi

# version: 0.1.0
