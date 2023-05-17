#!/bin/bash -eu
# find-linked

# Find file under . with more than one hard link (not dirs, files)
# output inode number then filename, and sort by inode number I guess

find . -type f -links +1 -printf "%i %p\n" | sort -n
