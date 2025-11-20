#!/bin/bash
#PARALLEL_MAX=${PARALLEL_MAX:-2}
while read A; do
	. para wget-scrape "$@" "$A"
done
wait
