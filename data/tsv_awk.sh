#!/bin/bash -eu
# run awk with options for TSV
prog="$1"
shift
awk 'BEGIN { FS="\t"; OFS="\t"; SUBSEP="\t" }'"$prog" "$@"
