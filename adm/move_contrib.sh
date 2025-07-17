#!/bin/bash -eu
cd "$ALLEMANDE_ROOMS"
mkdir -p contrib
find -path './contrib' -prune -o -name '*.safetensors' -print | xa vm "$ALLEMANDE_ROOMS/contrib"
