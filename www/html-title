#!/usr/bin/perl -n
# this is stupidly un-general, but I'm in a hurry

BEGIN {
    $/ = undef;
}

if (/<title\b.*?>(.*?)<\/title>/i) {
    print "$1\n";
    exit;
}
