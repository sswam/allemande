#!/bin/bash -eu
# This is a new shell to be!

. opts

cmd=()
cmd=(-c "$(printf "%q " "$@")")

bash "${OPTS[@]}" "${cmd[@]}"
