#!/bin/bash
# ped: perl wrapper to be as convenient as sed
# example: ped 's/he/she/; p'
. opts
perl "${OPTS_UNKNOWN[@]}" -n -e 'sub p { my $l = 0+@_ ? "$@\n" : $_; chomp $l; print "$l\n"; } '"$@"
