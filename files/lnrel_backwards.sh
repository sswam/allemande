#!/usr/bin/env bash
# dest [src1 ...]
# Create relative symbolic links to the source files.
DEST="$1"
shift
DIR="$DEST"
if [ ! -d "$DIR" ] && ! [[ "$DIR" == */ ]]; then
    DIR=$(dirname "$DEST")
fi
if [ ! -d "$DIR" ]; then
    echo "Error: Destination directory '$DIR' does not exist."
    exit 1
fi
for SRC; do
    ABS=$(realpath --canonicalize-missing "$SRC")
    RELPATH=$(realpath --relative-to="$DIR" "$ABS")
    ln -s "$RELPATH" "$DEST"
done
