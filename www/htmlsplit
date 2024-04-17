#!/usr/bin/perl
#use HTML::Entities;
#$_ = join "",<STDIN>; tr/\n\r \t/ /s; s/</\n</g; s/>/>\n/g; s/\n ?\n/\n/g; s/^ ?\n//s; s/ $//s; print
#$_ = join "",<STDIN>; s/</\n</g; 1 while s/^(<[^>]*)\n/$1 /gm; s/>/>\n/g; s/\n\s*\n/\n/gs; s/^\s*\n//s; s/\s*\z//s; s/^([^<].*)/decode_entities($1)/gme; print "$_\n"
$_ = join "",<STDIN>; s/</\n</g; 1 while s/^(<[^>]*)\n/$1 /gm; s/>/>\n/g; s/\n\s*\n/\n/gs; s/^\s*\n//s; s/\s*\z//s; print "$_\n"
