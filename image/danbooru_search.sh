#!/bin/bash
if (( $# )); then
	lecho "$@" | "$0"
	exit
fi
while read A; do grep "$A" ~/danbooru_tags_post_count.csv | less; done
