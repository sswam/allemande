#!/bin/bash
# prompt [file ...]
# A script to brainstorm something with AI

model= m=	# AI model

. opts

prompt="${1:-}"
shift || true

cat-named -b -p "$@" |
llm process --empty-ok -m="$model" "Brainstorm ideas based on the following prompt: $prompt"
