#!/bin/bash
# ki: keep input

# I'm using this with AI filters from vim, to keep the input in addition to the output.
# See also kia, which puts the input after the output.

# example:
# lecho "hello" "world" | ki wc

file=$(mktemp)
trap "rm -f $file" EXIT
cat > "$file"
cat "$file"
echo
< "$file" "$@"
