#!/bin/bash
set -e -u -o pipefail

# v opal -- ally-commit -v -N
v i rooms/ git restore --staged . || true
v i rooms/ git restore . || true
v i rooms/ git pull ucm.dev:$ALLEMANDE_HOME/rooms || true

# TODO do this more safely
time v sudo rs --exclude="*.html" ucm.dev:$ALLEMANDE_HOME/rooms/ rooms/ || true
time v sudo rs ucm.dev:$ALLEMANDE_HOME/ally-git/ $ALLEMANDE_HOME/ally-git/ || true   # TODO use git for this???!!!!111

echo
echo
v opal -- remove-old-media-from-rooms -y
v opal re

# backup_suffix_timestamp=$(date +%Y%m%d%H%M%S)
# time v sudo rs --backup --suffix=~$backup_suffix_timestamp~ ucm.dev:rooms/ rooms/
