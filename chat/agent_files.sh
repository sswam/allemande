#!/bin/bash -eu
find "$ALLEMANDE_AGENTS/" "$ALLEMANDE_ROOMS/" -path "*/agents/*" -type f -name "*.yml"
