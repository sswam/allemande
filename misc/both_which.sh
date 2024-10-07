#!/bin/bash -eu
# both-which:	work out which of tourism and industry an item should belong too, erring on the side of industry
joine  <(< tourism-list.txt kut 2 1 | order 1 ) <(< industry-list.txt kut 2 1 | order 1 ) | awk -F'\t' 'BEGIN { OFS="\t" } $2>$3 { $4="tourism" } $3>=$2 { $4="industry" } { print }' > which.txt
