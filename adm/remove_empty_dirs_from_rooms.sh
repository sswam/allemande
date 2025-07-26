#!/bin/bash -eu
find "$ALLEMANDE_ROOMS" -path '*/.*' -prune -o -type d -empty -print | xa rmdir -p --ignore-fail-on-non-empty
