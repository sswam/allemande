#!/bin/bash -eu
# rstrip:	Remove trailing white space on each line, and trailing blank lines from a file, ensuring it ends with a single newline

# This doesn't work if combined into one sed command; who knows why?
sed 's/[[:space:]]*$//;' | sed ':a; /^\n*$/ {$d; N; ba}' | awk 1 ORS='\n'
# 1. `:a` creates a label 'a' that we can jump back to.
# 2. `/^\n*$/` matches lines that are either empty or contain only newlines.
# 3. `{...}` groups the commands to be executed when the pattern matches.
# 4. `$d` deletes the line if it's the last line of the input.
# 5. `N` appends the next line to the pattern space.
# 6. `ba` branches (jumps) back to label 'a'.
