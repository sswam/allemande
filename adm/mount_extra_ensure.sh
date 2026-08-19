#!/bin/bash
count=$(timeout 10s sh -c 'ls /opt/allemande/rooms.extra | wc -l')
if [ -z "$count" -o "$count" = 0 ]; then
	q mount-extra
fi
