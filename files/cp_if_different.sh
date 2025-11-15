#!/bin/bash -eu
[ "$#" = 2 ]
q cmp "$1" "$2" || cp -a "$1" "$2"
