#!/bin/bash
# cr - copy to rubbish
# this is exactly `mr' but copying instead of moving
if [ -z "$RUBBISH" ]; then
	M=`mount-point "$1"`
	if [ "$M" = "$(mount-point "$HOME")" ]; then
		RUBBISH="$HOME/.rubbish"
	else
		RUBBISH="$M/.rubbish"
	fi
fi
(umask 0700; mkdir -p "$RUBBISH"; chmod 0700 "$RUBBISH")
for A; do
	N=`basename -- "$A"`
	while true; do
		timestamp=$(date "+%Y%m%d_%H%M%S%N%z_%a" | tr '[:upper:]' '[:lower:]')
		B="$RUBBISH/${N}_${timestamp}_$$"
		[ -e "$B" ] || break  # XXX not entirely secure, should use >| to creat or something?
	done
	cp -i -- "$A" "$B" || exit 1
	[ -n "$mr_echo" ] && echo "$B"
done
exit 0
