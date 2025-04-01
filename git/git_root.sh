#!/bin/sh
# git-root: print the root of the current git repository
cd "${1:-.}"
exec git rev-parse --show-toplevel
