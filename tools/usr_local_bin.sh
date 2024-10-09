#!/bin/bash
# [file ...]
# symlink files to /usr/local/bin
for file; do
	ln -sf "$(realpath -s "$file")" /usr/local/bin/
done
