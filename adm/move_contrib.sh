#!/bin/bash -eu

# Set source and destination directories
SRC_DIR="$ALLEMANDE_ROOMS_SERVER/contrib"
DEST_DIR="$ALLEMANDE_LORA"

for file in "$SRC_DIR"/*.safetensors; do
	if [ ! -f "$file" ]; then
		continue
	fi

	mv -nv "$file" "$DEST_DIR/"
	if [ -e "$file" ]; then
		rm -fv "$file"
	fi
done
