#!/bin/bash -eu
# [arg ...]

OPTS_ALLOW_UNKNOWN=1
name=

. opts

if [ "$PWD" = "$HOME" ]; then
	project_dir=$(readlink -f ~/project)
	cd "$project_dir" 2>/dev/null || true
fi

# build the command from argv using printf %q or what
cmd=()
if [ "$#" -gt 0 ]; then
	cmd=(-e "$@")
fi

x-terminal-emulator -name "$name" "${OPTS_UNKNOWN[@]}" "${cmd[@]}"
