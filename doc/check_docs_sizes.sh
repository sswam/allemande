#!/bin/bash -eu
# check that docs generation did not fail and leave empty files

. /opt/allemande/env.sh
cd "$ALLEMANDE_ROOMS"
if (wc -l intro.* guide.* intro_nsfw.* guide_nsfw.* 2>&1 || true) | grep -w -e 0 -e "^wc"; then
	echo "Oh no!"
	for F in intro.* guide.* intro_nsfw.* guide_nsfw.*; do
		# remove if empty
		if [ ! -s "$F" ]; then
			rm -f "$F"
		fi
	done
	cd "$ALLEMANDE_HOME/doc"
	make up
	exit 1
fi
