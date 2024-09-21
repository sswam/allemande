#!/bin/bash -eu
# giles1: search and summarise, a "one liner" version of giles proper

n=6
m="in one sentance please"
s="Please summarise everything relevant to %s"
m=
. opts

q=${*:-"When did GPT-3 come out; -ChatGPT"}
s=`printf "$s" "$q"`
. mdcd `slugify "$q"`
search -m "$n" "$q" | kut 2 | tail -n +2 | wgall
for f in *; do
	< "$f" pandoc -f html -t markdown |
		process -m="$m" "$s"
done |
process "$q $m"
