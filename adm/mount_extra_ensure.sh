#!/bin/bash
count=$(timeout 10s sh -c 'ls /opt/allemande/rooms.extra | wc -l')
if [ -z "$count" -o "$count" = 0 ] || ! mountpoint -q /opt/allemande/rooms.extra || ! mountpoint -q /opt/allemande/rooms.extra.raw; then
	qos mount-extra
fi
