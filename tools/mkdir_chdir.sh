#!/bin/bash
# make a directory if needed and cd into it
eval "$(ally)"
mkdir -p "$@" && cd "$@"
