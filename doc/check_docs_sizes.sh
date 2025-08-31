#!/bin/bash -eu
# check that docs generation did not fail and leave empty files

. /opt/allemande/env.sh

cd "$ALLEMANDE_ROOMS"
if wc -l intro.* guide.* nsfw/intro.* nsfw/guide.* | grep -w 0; then
	echo "Oh no!"
	exit 1
fi
