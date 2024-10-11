#!/usr/bin/env bash
# cat file.tsv | xargs_tsv.sh cmd [arg ...]
# xargs with a newline delimiter, each line tab separated goes to one invocation

eval "$(ally)"

IFS=$'\t'
while read -r line; do
	"$@" $line
done
