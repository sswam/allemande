#!/bin/bash -eu
cd "$ALLEMANDE_HOME"
mkdir -p rooms.extra
fusermount -u rooms.extra || true
sshfs -o allow_other -p 2222 localhost:rooms/ rooms.extra
