#!/usr/bin/perl -n
# pandoc-dump-clean - clean up pandoc HTML to markdown dump

use strict;
use warnings;

chomp;

s/\\$//;    # remove backslash from end of line
s/{.*?}//g;	# remove pandoc footnotes
s{\[(Like|Comment|Most relevant|Share|Log in|Posts|About|Photos|Videos|More)\]}{}g;	# remove facebook buttons
# s{(\bAll reactions:|### \d+ comments\b|\bSee more\b)}{}g;	# remove other facebook guff TODO fix this
s/^-? *:::.*//;	# remove pandoc divs
s/<.*?>//g;	# remove html tags
s/!(\[.*?\])?\(.*?\)//g;	# remove images
s{(https?://\S+?)\?[^\s\)"']*}{$1}g;	# remove query strings from urls
s{(\(/\S+?)\?[^\s\)"']*}{\($1}g;	# remove query strings from relative urls
s{\((https://www.facebook.com)?/photo/|https://l.facebook.com/l.php\)}{}g;	# remove facebook photos
s{\[([^]]+?)\]\(([^)]+?) "([^"]*?)"\)}{[$1]($2)}g;	# remove markdown link titles

1 while s/\[+[\s\d]*\]+//g;	# remove empty square brackets
s/[\[\(\{\(\<]+$//g;	# remove broken brackets
s/^[\]\)\}\>]+//g;	# remove broken brackets
s/\s+/ /g;	# remove extra whitespace
s/^\s+$//;	# remove spaces from empty lines
s/-{4,}/---/g;	# shorten lines of dashes, e.g. table row lines
s/_{4,}/___/g;	# shorten lines of underscores
s/={4,}/===/g;	# shorten lines of equals signs
s/^[-_=+:| ]+$//;	# clear lines that are only drawing horizontal lines and such
s{\^(\[\\\[\d+\\\]\]\(#cite_note[^)]*?\))+\^}{}g;	# remove wikipedia cite notes

my $ok = 1;
$ok &&= !/\bdata:image\b/;    # remove lines with image data, TODO where was this needed, can we do it better?

print "$_\n" if $ok;
