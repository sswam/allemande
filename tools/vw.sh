#!/bin/bash
## Q TODO move the options to the start, don't `which' them.  A better options system for unix/shell - how...???
##!/lang/perl
#use IO::File;
#
#for $a (@ARGV) {
#  -e $a || IO::File->open(
#}
#for A in "$@"
set +a
IFS='
'
exec ${EDITOR:-vi} -O $(p `wich "$@"`)
