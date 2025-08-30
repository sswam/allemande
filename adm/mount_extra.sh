#!/bin/bash -eu
cd "$ALLEMANDE_HOME"
mkdir -p rooms.extra || true
pkill -f "sshfs.*rooms.extra" || true
fusermount -u rooms.extra || true
# sshfs -o allow_other -p 2222 localhost:rooms/ rooms.extra
# TODO not hard code VPN IP address
sshfs -o allow_other 10.0.0.2:rooms/ rooms.extra
