#!/bin/bash -eu

. /opt/allemande/env.sh

arcs-sub "$@" "$ALLEMANDE_AGENTS"
arcs-sub "$@" "$ALLEMANDE_ROOMS"
