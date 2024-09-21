#!/bin/bash

# [reference files ...]
# Generate AI flashcard topics for a given audience

flash_gen() {
	local m=     # LLM model
	local n=100  # number of flashcards to generate
	local aud="programmers"
	local adj="illuminating"
	local topic="deep learning"
	local types="concepts, terms, and other topics"

	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	if [ -n "$n" ]; then
		n=" $n"
	fi
	if [ -n "$adj" ]; then
		adj=" $adj"
	fi
	if [ -n "$topic" ]; then
		topic=", about $topic"
	fi
	if [ -n "$aud" ]; then
		aud=", for $aud"
	fi
	if [ -n "$types" ]; then
		types=" Please cover the main $types, with definitions suitable for flashcard study."
	fi

	local refs=("$@")

	local refs_prompt=""
	if [ "${#refs[@]}" -gt 0 ]; then
		refs_prompt="Reference material: "
	fi

	local prompt2=$(cat <<END
Generate$n$adj flashcard topics$aud$topic.$types Please highlight the main
terms in bold. Each topic on the Front should be a numbered heading, and the
Back not numbered. The back should not contain the text of the topic. Format:

# 1. Front: The Topic.
Back: The answer (e.g. definition)'

# 2. ...
END
	)
	# clean up whitespace in the prompt
	prompt2=$(echo "$prompt2" | tr -s ' \n\t' ' ')

	local prompt1="$prompt2. $refs_prompt"

	local input=""
	if [ ${#refs[@]} -gt 0 ]; then
		input=$(cat_named.py -p -b "${refs[@]}")
	fi

	if [ -z "$input" ]; then
		input=":)"
		prompt2=""
	fi

	printf "%s\n" "$input" | llm process -m "$m" -P "$prompt2" "$prompt1"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	flash_gen "$@"
fi
