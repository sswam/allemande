#!/bin/awk -f
# secs2ago: Convert seconds since epoch to number of seconds/minutes/hours/days ago
BEGIN {
    FS=OFS="\t"
    now=systime()

    # Process command line arguments
    divisor = 1
    human = 0
    for (i = 1; i < ARGC; i++) {
        if (ARGV[i] == "--days") {
            divisor = 86400  # seconds in a day
            delete ARGV[i]
        } else if (ARGV[i] == "--hours") {
            divisor = 3600   # seconds in an hour
            delete ARGV[i]
        } else if (ARGV[i] == "--minutes") {
            divisor = 60     # seconds in a minute
            delete ARGV[i]
        } else if (ARGV[i] == "--human") {
            human = 1
            delete ARGV[i]
        }
    }
}
{
    diff = now - $1
    $1 = ""
    if (!human) {
        if (divisor > 1) {
            diff = int(diff / divisor)  # floor division
        }
        printf "%d%s\n", diff, $0
    } else {
        # Human readable format
        if (diff >= 86400) {
            printf "%dd%s\n", int(diff/86400), $0
        } else if (diff >= 3600) {
            printf "%dh%s\n", int(diff/3600), $0
        } else if (diff >= 60) {
            printf "%dm%s\n", int(diff/60), $0
        } else {
            printf "%ds%s\n", diff, $0
        }
    }
}
