#!/bin/sh
# [nl options]
# number all lines, including blank ones, in proper TSV
nl -b a -n ln -w 1 "$@"
