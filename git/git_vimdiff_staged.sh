#!/bin/sh

# v=v
# c=confirm

if [ "$#" = 0 -a -z "$VD_RECURSE" ]; then
	VD_RECURSE=1
	export VD_RECURSE
	git-mod staged | xa "$0"
	exit
fi
for F; do
	F=`readlink -f "$F"`
	O="`dirname "$F"`/.vd.`basename "$F"`"
	if v q git ls-files --error-unmatch "$F"; then
$v		cp "$F" "$O"
$v		git diff --staged $COMMIT -- "$F" | patch --quiet -R "$O"
	else
$v		git show HEAD:"$F" >"$O"
	fi
$c	vimdiff "$F" "$O" </dev/tty
	rm "$O"
done
