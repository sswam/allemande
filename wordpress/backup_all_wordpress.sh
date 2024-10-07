#!/bin/bash -eu
# backup named draft posts from wordpress

PARALLEL_MAX=20
t=post	# post or page

. opts

item_type=$t

bak=bak.`dttm`

mkdir "$bak"

while read D; do
	N=$(basename -- "$D")
	N=${N#- }
	S=$(slugify -H -l "$N")

	echo "*** BACKING UP WORDPRESS `echo "$t" | uc` $D"

	. para v injectify.py --read --$item_type --title "$N" --slug "$S" > "$bak/$N.json"
done
wait
