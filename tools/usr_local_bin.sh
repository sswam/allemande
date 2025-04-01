#!/bin/bash
# [file ...]
# symlink files to /usr/local/bin
. get-root
for file; do
	ln -sf "$(realpath -s "$file")" /usr/local/bin/
done
