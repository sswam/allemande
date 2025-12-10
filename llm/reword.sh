#!/bin/bash
m=s
n=1
p=
. opts
prompt="Please reword and rephrase this differently! Thanks for being awesome <3"
if [ -n "$n" ]; then
	prompt+=" Give $n option/s, just on separate lines/paragraphs, not numbered."
fi
prompt+=" $p"

process -m="$m" "$prompt"
