#!/bin/bash -eu
# clean up copy-pasted tags from danbooru website
sed '/^?$/d; s/ [^ ]*$//; s/[()]/\\&/g; s/ *$/,/' | tr '\n' ' ' | sed 's/, $/\n/'
