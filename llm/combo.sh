#!/bin/bash

# [input files]
# Combines similar inputs to get the best results

combine() {
	local model= m=  # LLM model
	local prompt= p= # Custom prompt

	eval "$(ally)"

	# Collect input files
	local input_files=("$@")

	local prompt="Combine the following inputs to create \
		a comprehensive and coherent result. $prompt"

	cat_named.py -p -b "${input_files[@]}" |
		process -m="$model" "$prompt"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	combine "$@"
fi
