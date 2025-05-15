#!/bin/awk -f
# secs2ago: Convert seconds since epoch to number of seconds ago
BEGIN {
    FS=OFS="\t"
    now=systime()
}
{
    diff = now - $1
    $1 = ""
    printf "%d%s\n", diff, $0
}
