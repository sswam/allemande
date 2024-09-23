#!/bin/bash
# [prompt] [options ...] < topics.md > notes.md
# Generate notes from a file of topics

. opts

prompt=$1 ; shift

run_batches.py -n 5 -- flash_gen.sh -n= -extra="Please make one numbered flashcard note corresponding to each numbered topic in the input. $prompt" "$@" -- -
