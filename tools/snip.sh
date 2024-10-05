#!/bin/bash -eu
# [file ...]
# Move files to snip/ directory.
mkdir -p snip/
mv -i "$@" snip/
