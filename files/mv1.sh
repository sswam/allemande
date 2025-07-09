#!/bin/bash -eu
# mv1: fromdir todir
set -e -u
from=${1:-~/Downloads/} to=${2:-.}
basename=$(ls1 "$from")
if [ "$basename" = STOP ]; then
	exit 1
fi
mv -vi "$from/$basename" "$to"/
