#!/bin/bash -eu

. /opt/allemande/env.sh

arcs-sub "$@" "$ALLEMANDE_AGENTS"
arcs-sub "$@" "$ALLEMANDE_ROOMS"
arcs-sub "$@" "$ALLEMANDE_USERS"
