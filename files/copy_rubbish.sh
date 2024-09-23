#!/bin/bash
# cr - copy to rubbish
# this is exactly `mr' but copying instead of moving
if [ -z "$RUBBISH" ]; then
	M=`mntpoint "$1"`
	if [ "$M" = "$(mntpoint "$HOME")" ]; then
		RUBBISH="$HOME/rubbish"
	else
		RUBBISH="$(mntpoint "$1")/rubbish"
	fi
fi
(umask 0700; mkdir -p "$RUBBISH"; chmod 0700 "$RUBBISH")
for A; do
	N=`basename -- "$A"`
	while true; do
		B="$RUBBISH/${N}_`nano=1 dt0`_$$"
		[ -e "$B" ] || break  # XXX not entirely secure, should use >| to creat or something?
	done
	cp -i -- "$A" "$B" || exit 1
	[ -n "$mr_echo" ] && echo "$B"
done
exit 0
