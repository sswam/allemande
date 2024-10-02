#!/bin/bash -eu
# [arg ...]
if [ "$PWD" = "$HOME" ]; then
	project_dir=$(readlink -f ~/project)
	cd "$project_dir" 2>/dev/null || true
fi
x-terminal-emulator "$@"
