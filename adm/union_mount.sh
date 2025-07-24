#!/bin/sh
cd $ALLEMANDE_HOME
union-umount
mkdir -p rooms.beorn
sshfs -o allow_other -p 2222 localhost:rooms/ rooms.beorn
sudo mount -t overlay overlay -o lowerdir="$ALLEMANDE_HOME/rooms.beorn",upperdir="$ALLEMANDE_HOME/rooms.opal",workdir="$ALLEMANDE_HOME/rooms.work" "$ALLEMANDE_ROOMS"
