#!/bin/sh
# xa: xargs with a newline delimiter
#xargs --no-run-if-empty -d'\n' "$@"
tr '\n' '\0' | xargs -r -0 "$@"
#perl -pe 's/\n/\0/gs' | xargs -0 --no-run-if-empty "$@"  # because allows \0 or \n for delimiter, sort of!
