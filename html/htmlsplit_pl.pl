#!/usr/bin/perl
$_ = join "",<STDIN>; s/</\n</g; 1 while s/^(<[^>]*)\n/$1 /gm; s/>/>\n/g; s/\n\s*\n/\n/gs; s/^\s*\n//s; s/\s*\z//s; print "$_\n"
