#!/bin/bash

# [reference files ...]
# Generate AI flashcards for a given audience

flash_gen() {
	local m=     # LLM model
	local n=10   # number of flashcards to generate
	local aud="programmers"
	local adj="illuminating"
	local topic="deep learning"
	local types="concepts, terms, and other topics"
	local extra=""

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
	if [ -n "$extra" ]; then
		extra=" $extra"
	fi

	local refs=("$@")

	local refs_prompt=""
	if [ "${#refs[@]}" -gt 0 ]; then
		refs_prompt="Reference material: "
	fi

	local prompt2=$(cat <<END
Generate$n$adj flashcard notes$aud$topic.$types Use markdown format with
TeX for math and \`\`\`code snippets\`\`\`, command samples, tables, links and markdown
images where appropriate. Embedded HTML fragments are okay if useful. You can
use mermaid graphviz or SVG for diagrams in some cards where appropriate.
Please highlight the main terms in bold. Each note should be numbered, and have
like '# 1. Front', '# 1. Back', and '# 1. Extra' sections. Front and Back
should be reversible. Front is generally a term, and Back is its 
definition (without using the text of the Term). Don't do it the other way around,
we will use the cards both ways but normally it's term -> definition.
Extra should contain additional details to display on the answer side. Double
newline between notes. Please produce rich and detailed flashcards, with plenty
of extra info.
$extra
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
	fi

	printf "%s\n" "$input" | llm process -m "$m" -P "$prompt2" "$prompt1"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	log "$0" "$@"
	flash_gen "$@"
fi
