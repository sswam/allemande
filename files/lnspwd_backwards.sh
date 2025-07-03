#!/usr/bin/env bash
# dest [src1 ...]
# Create aboslute symbolic links to the source files.
DEST="$1"
shift
for path; do
	ABS=$(realpath --canonicalize-missing "$path")
	ln -s "$ABS" "$DEST"
done
