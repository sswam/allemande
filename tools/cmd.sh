#!/bin/bash -eu
# [arg ...]
# dispatch to a subordinate command in a subdirectory

dir=$(dirname "$0")
base=$(basename "$0")
subdir=$dir/${base%.*}.d

sub=$1
shift

exec "$subdir/$sub" "$@"
exit 1
