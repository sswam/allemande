#!/bin/bash -eu
# [arg ...]
# dispatch to a subordinate command in a subdirectory

dir=$(dirname "$0")
base=$(basename "$0")
subdir=$dir/${base%.*}.d

case "${1:-}" in
""|-h|--help|help)
	ls -1 "$subdir"
	[ -n "${1:-}" ]
	exit 0
	;;
esac

sub=$1
shift

exec "$subdir/$sub" "$@"
exit 1
