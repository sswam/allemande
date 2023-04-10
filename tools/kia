#!/bin/bash
# kia: keep input after

# See also: ki: keep input

# example:
# lecho "hello" "world" | kia wc

file=$(mktemp)
trap "rm -f $file" EXIT
cat > "$file"
< "$file" "$@"
echo
cat "$file"
