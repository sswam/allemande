#!/bin/bash -eu
# llm-comment:	use an LLM to add comments to the code
m=
p="Please add short comments to explain the code, only when its not clear to an advanced programmer."
. opts
model=$m
prompt=$p
llm process -m "$model" "$prompt"
