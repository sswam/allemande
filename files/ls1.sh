#!/bin/bash -eu
# ls1: list the most recent file in a directory, or nth most recent
n=1
. opts
set -e -u
ls -t "$@" | line "$n"
