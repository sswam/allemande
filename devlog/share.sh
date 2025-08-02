#!/bin/bash

mkdir -p "$ALLEMANDE_ROOMS/devlog/tech"

for A in 20??-??-??.md; do
	BB="${A%.md}.bb"
	if [ -e "$ALLEMANDE_ROOMS/devlog/$BB" ]; then
		continue
	fi
	cp "$A" "tmp.bb"
	mv -v "tmp.bb" "$ALLEMANDE_ROOMS/devlog/tech/$BB"
	chmod -w "$ALLEMANDE_ROOMS/devlog/tech/$BB"
	cp "simple/$A" "tmp.bb"
	mv -v "tmp.bb" "$ALLEMANDE_ROOMS/devlog/$BB"
	chmod -w "$ALLEMANDE_ROOMS/devlog/$BB"
done
