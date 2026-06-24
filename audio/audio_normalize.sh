#!/bin/bash
for f in "$@"; do
  tmp=$(mktemp --suffix=".${f##*.}" )
  ffmpeg -i "$f" -af loudnorm -y "$tmp" && mv "$tmp" "$f"
  rm -f "$tmp"
done
