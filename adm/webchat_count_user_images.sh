#!/bin/bash -eu
cd "$ALLEMANDE_ROOMS"
find -name '*.jpg' | dirnames | sed 's/^\.\///' | sed 's/\/.*//' | uniqoc | sort -n
