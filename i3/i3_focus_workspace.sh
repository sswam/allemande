#!/bin/bash -eu
# i3-focus-workspace: Focus the parent workspace of the current window.
for i in {1..100}; do
	if ! q i3-msg focus parent; then
		break
	fi
done
