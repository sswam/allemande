#!/usr/bin/perl -n
# Description: Remove mulitple blank lines from a file

print unless /^$/ && $last_line_empty;
$last_line_empty = /^$/;
