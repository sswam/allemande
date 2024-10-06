#!/bin/bash
# psgrep: grep for a process
set -a
q=$*
q1=${q::1}
q2=${q:1}
# q1=`printf %q "${q::1}"`
# q2=`printf %q "${q:1}"`
COLUMNS=10000 exec sh -c 'ps aux | grep -i "[$q1]$q2"'
