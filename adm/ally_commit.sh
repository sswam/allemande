#!/bin/bash -eu

. /opt/allemande/env.sh

remove-empty-dirs-from-rooms
arcs-sub "$@" "$ALLEMANDE_AGENTS"
arcs-sub "$@" "$ALLEMANDE_ROOMS"
arcs-sub "$@" "$ALLEMANDE_USERS"
