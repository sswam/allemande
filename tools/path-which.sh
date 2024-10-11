#!/bin/bash
# [file ...]
# print where a command or file in PATH is located (e.g. shell lib, needed resource)
eval "$(ally)"
for A; do
	path-find "$(which-file "$A")"
done
