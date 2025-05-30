#!/usr/bin/env bash
# Categorize browser tabs saved in TSV files.
cat ~/Downloads/tabs*.tsv | uniqo | perl -pe 's{^(https://www\.google\.com/search\?q=.*?)&.*?\t}{$1\t}' | nla > tabs_numbered.tsv
< tabs_numbered.tsv process -m=gp "Please categorise these webpages, return only TSV with the line number followed by a short category or tag name in snake_case. Common prefixes for related tags are good. Not too many different categories is good." > cat.tsv
joine cat.tsv tabs_numbered.tsv | kutout 1 | order | undrool 1 | perl -pe 'chomp; @f = split /\t/, $_, -1; if ($f[0]) { print "\n## $f[0]\n"; }  $_ = "- [$f[2]]($f[1])\n";' > tabs.md
