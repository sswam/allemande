#!/bin/bash
# psgrep: grep for a process
set -a
for q; do
	q1=${q::1}
	q2=${q:1}
	COLUMNS=10000 ps aux | awk -v pid="$$" '$2 != pid' | grep -i "[$q1]$q2"
done
