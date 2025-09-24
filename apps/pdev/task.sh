#!/bin/bash -eu
# Use AI to categorize tasks into the Eisenhower Matrix.
cd ~/task
if [ "${1:-}" = -e ]; then
	exec vim -S task.vim
fi
cat-named --stdin-name "new tasks" comments.md mission.m [0-4]-*.md - |
process "Please categorize new tasks (only) into the Eisenhower Matrix, compactly, and strictly following the same format as the input but omitting empty sections." |
split-files -a -
