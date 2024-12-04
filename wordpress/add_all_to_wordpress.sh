#!/bin/bash -eu
# add all output.md to wordpress

PARALLEL_MAX=10
t=post	# post or page
T=template/tourism.txt	# template
# m=1347	# which image to use
m=	# media ID of featured image or blank for none
Y=	# do not add YouTube videos

. opts

item_type=$t
template=$T
media=$m
no_youtube=$Y

if [ -n "$media" ]; then
	media_opts="--media-default $media"
else
	media_opts=
fi

for D; do
	N=$(basename "$D")

	echo "*** PROCESSING $N"

	if [ "$no_youtube" = 1 ]; then
		v prettify.py -a "$N, South Gippland, Victoria" -t "$template" "$D"/output.*.md > "$D/wordpress.txt" || true
	else
		youtube_arg="$D/youtube.md"
		touch "$youtube_arg"
		v prettify.py -a "$N, South Gippland, Victoria" -t "$template" "$D"/output.*.md "$youtube_arg" > "$D/wordpress.txt" || true
	fi
done

mkdir -p DONE

for D; do
	N=$(basename "$D")
	S=$(slug -H -l "$N")

	echo "*** PUSHING TO WORDPRESS $D"

	. para v injectify.py --auto --$item_type --title "$N" --slug "$S" --file "$D/wordpress.txt" $media_opts || true
done
wait
