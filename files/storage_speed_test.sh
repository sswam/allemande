#!/bin/bash
dfh |
tail -n +2 |
while read mnt free use used size device; do
	echo -n "$mnt"$'\t'"$device"$'\t'
	sudo hdparm -t --direct "$device" |
	tail -n1 |
	sed 's/.*= //'
done
