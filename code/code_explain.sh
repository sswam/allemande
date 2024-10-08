#!/bin/bash -eu
m=
. opts
name="${1:-}"
prompt="Please explain this code in brief and what the tool is supposed to do, for an experienced senior developer. No need to explain line by line."
if [ -n "$name" ]; then
    prompt+=" The program is called $name."
fi
if [ -t 0 ] && [ -f "$name" ]; then
    exec < "$name"
fi
exec kia llm process -m "$m" "$prompt"
