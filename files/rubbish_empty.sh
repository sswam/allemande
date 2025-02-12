#!/bin/bash -e
# rubbish-empty: empty the rubbish bin
for BASE in "$HOME" $(qe df | tail -n +2 | awk '{print $6}'); do
	RUBBISH=$BASE/.rubbish
	if [ ! -d "$RUBBISH" ]; then
		continue
	fi
	cd "$RUBBISH"
	find -mindepth 1 -maxdepth 1 -print0 | xargs --no-run-if-empty -0 rm -f -v -r --
	# rmdir "$RUBBISH"
done
