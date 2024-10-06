#!/bin/bash -eu
# namer:	generate name ideas using an LLM

v=	# verbose
m=s	# which LLM model to use
n=10	# number of names to generate
q="Please come up with some interesting and unusual names, preferably spelled differently from any normal personal names. Single word human-like names, not compound words. Mostly short simple names please, not too long; but you can include some long fancy ones if they sound great. They do not have to be super-closely related to any prompt words; but not too crazy"	# query prompt
f="Please list %d options in a markdown list"	# format string for formatting part of the prompt
b="based on this prompt name or concept:\n\n*** Prompt name or concept: %s\n"	# based prompt
c="Please combine these into a single pronouncable name, syllable by syllable, e.g. TDD, Kent, Martin, Ron -> Karton"	# combine prompt

. opts

verbose=$v
model=$m
n_gen=$n
names=("$@")
n_inputs=${#names[@]}
query=$q
fmt=$f
based=$b
combine=$c

if [ -n "$v" ]; then
	v="v"
fi

if [ $n_inputs -eq 0 ]; then
	$v query -m=$model "`printf "$query. $fmt." "$n_gen"`"
elif [ $n_inputs -eq 1 ]; then
	$v query -m=$model "`printf "$query, $based\n$fmt" "${names[*]}" "$n_gen"`"
else
	list=""
	for name in "${names[@]}"; do
		list="$list- $name\n"
	done
	$v query "`printf "$query, $based\n$combine. $fmt." "$list" "$n_gen"`"
fi
