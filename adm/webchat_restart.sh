#!/bin/bash -eu
cd "$ALLEMANDE_HOME"
make stop
sshc vopal= make stop
sshc vopal= make server
make core
xt-allemande -r
